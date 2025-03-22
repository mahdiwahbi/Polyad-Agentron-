#!/usr/bin/env python3
import os
import json
import sqlite3
from typing import Any, Dict, List, Optional
from langchain_community.tools import DuckDuckGoSearchRun

class PolyadTools:
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialise les outils Polyad
        
        Args:
            cache_dir: Répertoire de cache
        """
        self.cache_dir = cache_dir
        self.cache_db = os.path.join(cache_dir, "polyad_cache.db")
        self.search_tool = DuckDuckGoSearchRun()
        
        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialiser la base de données de cache
        self._init_cache_db()
        
    def _init_cache_db(self):
        """Initialise la base de données de cache"""
        try:
            conn = sqlite3.connect(self.cache_db)
            c = conn.cursor()
            
            # Créer la table de cache si elle n'existe pas
            c.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Cache initialisé:", self.cache_db)
            
        except Exception as e:
            print("Erreur lors de l'initialisation du cache:", str(e))
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    def generate_text(self, prompt: str) -> str:
        """
        Génère du texte à partir d'un prompt
        
        Args:
            prompt: Le prompt à utiliser
            
        Returns:
            str: Le texte généré
        """
        # Vérifier dans le cache
        cached = self._get_from_cache(prompt)
        if cached:
            return cached
            
        # Générer le texte avec le modèle
        try:
            result = self.search_tool.run(prompt)
            
            # Mettre en cache
            self._save_to_cache(prompt, result)
            
            return result
            
        except Exception as e:
            print("Erreur lors de la génération de texte:", str(e))
            return ""
            
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Récupère une valeur du cache"""
        try:
            conn = sqlite3.connect(self.cache_db)
            c = conn.cursor()
            
            c.execute("SELECT value FROM cache WHERE key = ?", (key,))
            result = c.fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            print("Erreur lors de la lecture du cache:", str(e))
            return None
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    def _save_to_cache(self, key: str, value: str):
        """Sauvegarde une valeur dans le cache"""
        try:
            conn = sqlite3.connect(self.cache_db)
            c = conn.cursor()
            
            c.execute("""
                INSERT OR REPLACE INTO cache (key, value)
                VALUES (?, ?)
            """, (key, value))
            
            conn.commit()
            
        except Exception as e:
            print("Erreur lors de l'écriture dans le cache:", str(e))
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            conn = sqlite3.connect(self.cache_db)
            c = conn.cursor()
            
            # Supprimer les entrées anciennes
            c.execute("""
                DELETE FROM cache
                WHERE datetime(timestamp) < datetime('now', '-7 days')
            """)
            
            # Optimiser la base
            try:
                c.execute("VACUUM")
            except sqlite3.OperationalError as e:
                print("Erreur lors du nettoyage du cache:", str(e))
                
            conn.commit()
            print("Connexion à la base de données du cache fermée")
            
        except Exception as e:
            print("Erreur lors du nettoyage:", str(e))
            
        finally:
            if 'conn' in locals():
                conn.close()
                
        print("Nettoyage des ressources PolyadTools terminé")
