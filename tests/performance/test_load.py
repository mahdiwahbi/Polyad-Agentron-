import pytest
import asyncio
import time
from polyad.api.app import create_app
from polyad.core.agent import PolyadAgent
from polyad.core.cache.cache_manager import CacheManager
from polyad.core.optimization.network_optimizer import NetworkOptimizer
from polyad.core.security.encryption import EncryptionManager
from polyad.core.monitoring.monitoring_service import MonitoringService

@pytest.fixture
def test_client():
    """
    Client de test pour l'API
    """
    app = create_app()
    return app.test_client()

@pytest.fixture
def test_agent():
    """
    Agent de test
    """
    config = {
        'cache': {
            'size': 1024 * 1024 * 1024,  # 1GB
            'ttl': 60,  # 1 minute
            'cleanup_interval': 300  # 5 minutes
        },
        'gpu': {
            'memory_threshold': 0.8,
            'temperature_threshold': 80,
            'optimization_interval': 60
        },
        'network': {
            'upload_threshold': 10,  # Mbps
            'download_threshold': 100,  # Mbps
            'latency_threshold': 100,  # ms
            'packet_loss_threshold': 1,  # %
            'optimization_interval': 60  # secondes
        },
        'security': {
            'encryption_key': 'test_key',
            'salt': 'test_salt',
            'iterations': 100000
        },
        'monitoring': {
            'grafana': {
                'api_key': 'test_api_key',
                'host': 'localhost',
                'port': 3000
            },
            'metrics_interval': 1,
            'alert_thresholds': {
                'cpu': 90,
                'memory': 90,
                'temperature': 80
            }
        }
    }
    return PolyadAgent(config)

@pytest.fixture
def test_cache():
    """
    Cache de test
    """
    config = {
        'cache': {
            'size': 1024 * 1024 * 1024,  # 1GB
            'ttl': 60,  # 1 minute
            'cleanup_interval': 300  # 5 minutes
        }
    }
    return CacheManager(config)

@pytest.fixture
def test_network():
    """
    Network Optimizer de test
    """
    config = {
        'network': {
            'upload_threshold': 10,  # Mbps
            'download_threshold': 100,  # Mbps
            'latency_threshold': 100,  # ms
            'packet_loss_threshold': 1,  # %
            'optimization_interval': 60  # secondes
        }
    }
    return NetworkOptimizer(config)

@pytest.fixture
def test_security():
    """
    Encryption Manager de test
    """
    config = {
        'encryption_key': 'test_key',
        'salt': 'test_salt',
        'iterations': 100000
    }
    return EncryptionManager(config)

@pytest.fixture
def test_monitoring():
    """
    Monitoring Service de test
    """
    config = {
        'monitoring': {
            'grafana': {
                'api_key': 'test_api_key',
                'host': 'localhost',
                'port': 3000
            },
            'metrics_interval': 1,
            'alert_thresholds': {
                'cpu': 90,
                'memory': 90,
                'temperature': 80
            }
        }
    }
    return MonitoringService(config)


class TestLoad:
    """
    Tests de charge pour évaluer les performances
    """
    
    async def test_concurrent_requests(self, test_client, test_agent):
        """
        Teste les requêtes concurrentes
        """
        async def send_request():
            task = {
                'type': 'system',
                'action': 'monitor',
                'data': {
                    'components': ['cpu', 'memory', 'gpu']
                }
            }
            response = await test_client.post('/task', json=task)
            assert response.status_code == 200
            
        # Mesurer le temps de base
        start = time.time()
        await send_request()
        base_time = time.time() - start
        
        # Test avec 10 requêtes concurrentes
        tasks = [send_request() for _ in range(10)]
        start = time.time()
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start
        
        # Vérifier que le temps n'a pas augmenté de plus de 50%
        assert concurrent_time < base_time * 1.5

    async def test_cache_performance(self, test_cache):
        """
        Teste les performances du cache
        """
        # Préparer les données de test
        keys = [f"test_key_{i}" for i in range(1000)]
        values = [f"test_value_{i}" for i in range(1000)]
        
        # Mesurer le temps de set
        start = time.time()
        for key, value in zip(keys, values):
            await test_cache.set(key, value)
        set_time = time.time() - start
        
        # Mesurer le temps de get
        start = time.time()
        for key in keys:
            await test_cache.get(key)
        get_time = time.time() - start
        
        # Vérifier les performances
        assert set_time < 1.0  # moins de 1 seconde pour 1000 set
        assert get_time < 0.5  # moins de 0.5 seconde pour 1000 get

    async def test_network_performance(self, test_network):
        """
        Teste les performances réseau
        """
        # Mesurer les métriques initiales
        initial_metrics = test_network.get_metrics()
        
        # Simuler une charge élevée
        async def simulate_load():
            for _ in range(1000):
                await test_network._optimize_network()
        
        # Mesurer le temps de traitement
        start = time.time()
        await simulate_load()
        processing_time = time.time() - start
        
        # Vérifier les performances
        assert processing_time < 10.0  # moins de 10 secondes pour 1000 optimisations
        
        # Vérifier l'amélioration des métriques
        final_metrics = test_network.get_metrics()
        assert final_metrics['latency'] < initial_metrics['latency']
        assert final_metrics['packet_loss'] < initial_metrics['packet_loss']

    async def test_security_performance(self, test_security):
        """
        Teste les performances de sécurité
        """
        # Préparer les données sensibles
        sensitive_data = {
            'sensitive': 'confidential_data' * 1000  # 1000 fois la chaîne
        }
        
        # Mesurer le temps de chiffrement
        start = time.time()
        encrypted_data = test_security.encrypt(sensitive_data)
        encryption_time = time.time() - start
        
        # Mesurer le temps de déchiffrement
        start = time.time()
        decrypted_data = test_security.decrypt(encrypted_data)
        decryption_time = time.time() - start
        
        # Vérifier les performances
        assert encryption_time < 0.1  # moins de 100ms pour le chiffrement
        assert decryption_time < 0.1  # moins de 100ms pour le déchiffrement
        assert decrypted_data == sensitive_data

    async def test_monitoring_performance(self, test_monitoring):
        """
        Teste les performances de monitoring
        """
        # Simuler la collecte de métriques
        async def collect_metrics():
            for _ in range(1000):
                test_monitoring.collect_metrics()
        
        # Mesurer le temps de collecte
        start = time.time()
        await collect_metrics()
        collection_time = time.time() - start
        
        # Vérifier les performances
        assert collection_time < 1.0  # moins de 1 seconde pour 1000 collectes
        
        # Vérifier l'exactitude des métriques
        metrics = test_monitoring.get_metrics()
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'gpu' in metrics
        assert 'network' in metrics

    async def test_resource_usage(self, test_agent):
        """
        Teste l'utilisation des ressources
        """
        import psutil
        
        # Obtenir l'utilisation initiale
        initial_cpu = psutil.cpu_percent()
        initial_memory = psutil.virtual_memory().percent
        
        # Simuler une charge élevée
        async def simulate_load():
            for _ in range(1000):
                await test_agent.process_request({
                    'type': 'system',
                    'action': 'monitor',
                    'data': {
                        'components': ['cpu', 'memory', 'gpu']
                    }
                })
        
        # Mesurer l'utilisation des ressources
        await simulate_load()
        final_cpu = psutil.cpu_percent()
        final_memory = psutil.virtual_memory().percent
        
        # Vérifier que l'utilisation n'a pas augmenté de plus de 50%
        assert final_cpu < initial_cpu * 1.5
        assert final_memory < initial_memory * 1.5

    async def test_resilience(self, test_agent):
        """
        Teste la résilience du système
        """
        # Simuler une erreur
        async def simulate_error():
            try:
                await test_agent.process_request({
                    'type': 'invalid',
                    'action': 'invalid',
                    'data': {}
                })
            except Exception as e:
                assert isinstance(e, ValueError)
                
        # Simuler plusieurs erreurs
        for _ in range(100):
            await simulate_error()
            
        # Vérifier que le système reste fonctionnel
        response = await test_agent.process_request({
            'type': 'system',
            'action': 'monitor',
            'data': {
                'components': ['cpu', 'memory', 'gpu']
            }
        })
        assert response.get('status') == 'success'
