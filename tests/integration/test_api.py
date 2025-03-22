import pytest
import requests
from polyad.api.app import create_app
from polyad.core.agent import PolyadAgent
from polyad.core.cache.cache_manager import CacheManager
from polyad.core.optimization.gpu_optimizer import GPUOptimizer
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
def test_gpu():
    """
    GPU Optimizer de test
    """
    config = {
        'gpu': {
            'memory_threshold': 0.8,
            'temperature_threshold': 80,
            'optimization_interval': 60
        }
    }
    return GPUOptimizer(config)

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


class TestAPI:
    """
    Tests d'intégration pour l'API
    """
    
    def test_status_endpoint(self, test_client):
        """
        Teste l'endpoint /status
        """
        response = test_client.get('/status')
        assert response.status_code == 200
        assert 'status' in response.json()
        assert 'uptime' in response.json()
        assert 'resources' in response.json()
        assert 'cache' in response.json()

    def test_task_submission(self, test_client, test_agent):
        """
        Teste la soumission de tâches
        """
        task = {
            'type': 'system',
            'action': 'monitor',
            'data': {
                'components': ['cpu', 'memory', 'gpu']
            }
        }
        response = test_client.post('/task', json=task)
        assert response.status_code == 200
        assert 'task_id' in response.json()
        assert 'status' in response.json()
        assert 'estimated_time' in response.json()

    def test_metrics_endpoint(self, test_client):
        """
        Teste l'endpoint /metrics
        """
        response = test_client.get('/metrics')
        assert response.status_code == 200
        assert 'cpu' in response.json()
        assert 'memory' in response.json()
        assert 'gpu' in response.json()
        assert 'network' in response.json()

    def test_cache_endpoint(self, test_client):
        """
        Teste l'endpoint /cache
        """
        response = test_client.get('/cache')
        assert response.status_code == 200
        assert 'size' in response.json()
        assert 'hits' in response.json()
        assert 'misses' in response.json()
        assert 'hit_rate' in response.json()
        assert 'evictions' in response.json()

    def test_security(self, test_client, test_security):
        """
        Teste la sécurité de l'API
        """
        # Teste l'authentification
        response = test_client.get('/status')
        assert response.status_code == 401
        
        # Teste le chiffrement
        sensitive_data = {
            'sensitive': 'confidential_data'
        }
        encrypted_data = test_security.encrypt(sensitive_data)
        assert encrypted_data != sensitive_data
        assert test_security.decrypt(encrypted_data) == sensitive_data

    def test_performance(self, test_client, test_cache):
        """
        Teste les performances de l'API
        """
        # Teste les performances du cache
        key = "test_key"
        value = "test_value"
        
        # Mesure du temps de set
        start = time.time()
        response = test_client.post(f'/cache/{key}', json={'value': value})
        set_time = time.time() - start
        assert response.status_code == 200
        assert set_time < 0.1  # moins de 100ms
        
        # Mesure du temps de get
        start = time.time()
        response = test_client.get(f'/cache/{key}')
        get_time = time.time() - start
        assert response.status_code == 200
        assert get_time < 0.1  # moins de 100ms
