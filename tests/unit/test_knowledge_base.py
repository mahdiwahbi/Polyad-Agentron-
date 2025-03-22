import pytest
import os
import json
import numpy as np
import sqlite3
import asyncio
from unittest.mock import patch, MagicMock

from core.knowledge_base import KnowledgeBase

@pytest.fixture
def knowledge_base():
    """Fixture pour créer une base de connaissances de test"""
    # Utiliser une base de données en mémoire pour les tests
    kb = KnowledgeBase(db_path=":memory:")
    return kb

@pytest.fixture
async def initialized_kb(knowledge_base):
    """Fixture pour une base de connaissances initialisée"""
    await knowledge_base.initialize()
    return knowledge_base

@pytest.mark.asyncio
async def test_initialization(knowledge_base):
    """Tester l'initialisation de la base de connaissances"""
    result = await knowledge_base.initialize()
    assert result is True
    assert knowledge_base.conn is not None
    assert knowledge_base.vector_store is not None

@pytest.mark.asyncio
async def test_add_entry(initialized_kb):
    """Tester l'ajout d'une entrée dans la base de connaissances"""
    # Créer une entrée de test
    test_entry = {
        "type": "text",
        "content": "Ceci est un test",
        "metadata": {
            "source": "test",
            "timestamp": "2025-03-21T00:00:00Z"
        }
    }
    
    # Ajouter l'entrée
    result = await initialized_kb.add_entry(test_entry)
    assert result is True
    
    # Vérifier que l'entrée a été ajoutée
    count = initialized_kb.__len__()
    assert count == 1

@pytest.mark.asyncio
async def test_search(initialized_kb):
    """Tester la recherche dans la base de connaissances"""
    # Ajouter plusieurs entrées
    entries = [
        {
            "type": "text",
            "content": "L'intelligence artificielle est un domaine passionnant",
            "metadata": {"source": "article"}
        },
        {
            "type": "text",
            "content": "Les réseaux de neurones sont utilisés en apprentissage profond",
            "metadata": {"source": "livre"}
        },
        {
            "type": "text",
            "content": "Python est un langage de programmation populaire",
            "metadata": {"source": "tutoriel"}
        }
    ]
    
    for entry in entries:
        await initialized_kb.add_entry(entry)
    
    # Rechercher des entrées similaires
    results = await initialized_kb.search("intelligence artificielle")
    assert len(results) > 0
    
    # La première entrée devrait être la plus pertinente
    assert "intelligence artificielle" in json.loads(results[0]['content'])['content'].lower()

@pytest.mark.asyncio
async def test_embedding_generation(initialized_kb):
    """Tester la génération d'embeddings"""
    # Tester avec différents textes
    texts = [
        "Bonjour, comment ça va?",
        "L'intelligence artificielle est fascinante",
        "Python est un excellent langage de programmation"
    ]
    
    for text in texts:
        embedding = await initialized_kb._get_embedding(text)
        
        # Vérifier les dimensions et le type
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        
        # Vérifier que les valeurs sont normalisées
        assert np.all(embedding >= 0) and np.all(embedding <= 1)
        
        # Vérifier que des textes différents donnent des embeddings différents
        other_embedding = await initialized_kb._get_embedding("Un texte complètement différent")
        assert not np.array_equal(embedding, other_embedding)

@pytest.mark.asyncio
async def test_close(initialized_kb):
    """Tester la fermeture de la connexion"""
    await initialized_kb.close()
    
    # Vérifier que la connexion est fermée
    with pytest.raises(Exception):
        initialized_kb.conn.execute("SELECT 1")
