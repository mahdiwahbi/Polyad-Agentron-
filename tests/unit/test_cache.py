import pytest
from polyad.core.cache.cache_manager import CacheManager
from polyad.core.security.encryption import EncryptionManager
import time

@pytest.fixture
def cache_manager():
    """
    Fixtures pour le CacheManager
    """
    config = {
        'cache': {
            'size': 1024 * 1024 * 1024,  # 1GB
            'ttl': 60,  # 1 minute
            'cleanup_interval': 300  # 5 minutes
        },
        'security': {
            'encryption_key': 'test_key',
            'salt': 'test_salt',
            'iterations': 100000
        }
    }
    return CacheManager(config)

@pytest.fixture
def encryption_manager():
    """
    Fixtures pour l'EncryptionManager
    """
    config = {
        'encryption_key': 'test_key',
        'salt': 'test_salt',
        'iterations': 100000
    }
    return EncryptionManager(config)


class TestCacheManager:
    """
    Tests unitaires pour le CacheManager
    """
    
    async def test_cache_operations(self, cache_manager):
        """
        Teste les opérations de cache
        """
        key = "test_key"
        value = "test_value"
        
        # Test du set
        assert await cache_manager.set(key, value)
        
        # Test du get
        assert await cache_manager.get(key) == value
        
        # Test du delete
        assert await cache_manager.delete(key)
        assert await cache_manager.get(key) is None

    async def test_sensitive_data(self, cache_manager, encryption_manager):
        """
        Teste le chiffrement des données sensibles
        """
        key = "sensitive_key"
        sensitive_data = {
            'sensitive': 'confidential_data'
        }
        
        # Stocker les données sensibles
        assert await cache_manager.set(key, sensitive_data)
        
        # Récupérer et vérifier le déchiffrement
        retrieved_data = await cache_manager.get(key)
        assert isinstance(retrieved_data, dict)
        assert 'sensitive' in retrieved_data
        assert retrieved_data['sensitive'] == sensitive_data['sensitive']

    async def test_ttl(self, cache_manager):
        """
        Teste le TTL du cache
        """
        key = "ttl_key"
        value = "test_value"
        
        # Stocker avec TTL court
        assert await cache_manager.set(key, value, ttl=1)
        
        # Attendre que le TTL expire
        await asyncio.sleep(2)
        
        # Vérifier que la valeur a expiré
        assert await cache_manager.get(key) is None

    async def test_cleanup(self, cache_manager):
        """
        Teste le nettoyage du cache
        """
        # Stocker plusieurs valeurs
        for i in range(10):
            key = f"test_key_{i}"
            value = f"test_value_{i}"
            assert await cache_manager.set(key, value)
            
        # Attendre l'intervalle de nettoyage
        await asyncio.sleep(300)
        
        # Vérifier que les valeurs ont été nettoyées
        for i in range(10):
            key = f"test_key_{i}"
            assert await cache_manager.get(key) is None

    async def test_stats(self, cache_manager):
        """
        Teste les statistiques du cache
        """
        key = "stats_key"
        value = "test_value"
        
        # Obtenir les stats initiales
        stats = cache_manager.get_stats()
        assert 'size' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        
        # Effectuer des opérations
        assert await cache_manager.set(key, value)
        assert await cache_manager.get(key)
        
        # Vérifier les stats mises à jour
        updated_stats = cache_manager.get_stats()
        assert updated_stats['hits'] > stats['hits']
        assert updated_stats['misses'] == stats['misses']
