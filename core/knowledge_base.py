import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import faiss
import numpy as np
from utils.logger import logger

class KnowledgeBase:
    """Base de connaissances avec RAG et apprentissage continu"""
    
    def __init__(self, db_path: str = "data/knowledge.db"):
        self.db_path = db_path
        self.conn = None
        self.vector_store = None
        
    async def initialize(self):
        """Initialiser la base de connaissances"""
        try:
            # Créer le répertoire data si nécessaire
            os.makedirs("data", exist_ok=True)
            
            # Initialiser SQLite
            self.conn = sqlite3.connect(self.db_path)
            self._create_tables()
            
            # Initialiser FAISS
            self.vector_store = faiss.IndexFlatL2(384)  # Dimension des embeddings
            
            # Charger les embeddings existants
            self._load_embeddings()
            
            logger.info("Base de connaissances initialisée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'initialisation de la base: {e}")
            return False
            
    def _create_tables(self):
        """Créer les tables nécessaires"""
        with self.conn:
            # Table des connaissances
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des embeddings
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vector BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
    def _load_embeddings(self):
        """Charger les embeddings existants dans FAISS"""
        try:
            embeddings = self.conn.execute(
                "SELECT id, vector FROM embeddings"
            ).fetchall()
            
            if embeddings:
                vectors = []
                for _, vector in embeddings:
                    vectors.append(np.frombuffer(vector, dtype=np.float32))
                vectors = np.vstack(vectors)
                self.vector_store.add(vectors)
                
        except Exception as e:
            logger.error(f"Erreur de chargement des embeddings: {e}")
            
    async def add_entry(self, entry: Dict[str, Any]):
        """Ajouter une entrée dans la base"""
        try:
            # Convertir en JSON pour stockage
            content = json.dumps(entry)
            metadata = json.dumps({
                'timestamp': datetime.now().isoformat(),
                'type': entry.get('type', 'unknown')
            })
            
            # Obtenir l'embedding
            embedding = await self._get_embedding(content)
            
            # Sauvegarder l'embedding
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO embeddings (vector) VALUES (?)",
                    (embedding.tobytes(),)
                )
                embedding_id = cursor.lastrowid
                
                # Sauvegarder l'entrée
                cursor.execute(
                    """
                    INSERT INTO knowledge 
                    (type, content, metadata, embedding_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (entry.get('type', 'unknown'), content, metadata, embedding_id)
                )
                
            # Ajouter à FAISS
            self.vector_store.add(embedding.reshape(1, -1))
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'ajout d'entrée: {e}")
            return False
            
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Rechercher des entrées similaires"""
        try:
            # Obtenir l'embedding de la requête
            query_embedding = await self._get_embedding(query)
            
            # Rechercher dans FAISS
            D, I = self.vector_store.search(
                query_embedding.reshape(1, -1),
                k
            )
            
            # Récupérer les entrées
            results = []
            for idx in I[0]:
                entry = self.conn.execute(
                    """
                    SELECT content, metadata
                    FROM knowledge
                    WHERE embedding_id = ?
                    """,
                    (int(idx) + 1,)  # FAISS indices start at 0
                ).fetchone()
                
                if entry:
                    content = json.loads(entry[0])
                    metadata = json.loads(entry[1])
                    results.append({
                        'content': content,
                        'metadata': metadata
                    })
                    
            return results
            
        except Exception as e:
            logger.error(f"Erreur de recherche: {e}")
            return []
            
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Obtenir l'embedding d'un texte"""
        # Utiliser un hachage simple pour générer un embedding
        import hashlib
        
        # Créer un hash SHA-256 du texte
        hash_object = hashlib.sha256(text.encode())
        hash_bytes = hash_object.digest()
        
        # Convertir en tableau numpy et redimensionner à 384 dimensions
        embedding = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
        embedding = embedding / 255.0  # Normaliser entre 0 et 1
        
        # Répéter ou tronquer pour obtenir 384 dimensions
        if len(embedding) < 384:
            embedding = np.tile(embedding, 384 // len(embedding) + 1)[:384]
        else:
            embedding = embedding[:384]
            
        return embedding
        
    def __len__(self):
        """Nombre d'entrées dans la base"""
        return self.conn.execute(
            "SELECT COUNT(*) FROM knowledge"
        ).fetchone()[0]
        
    async def close(self):
        """Fermer la connexion"""
        if self.conn:
            self.conn.close()
