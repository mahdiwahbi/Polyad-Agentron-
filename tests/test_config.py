import os
import unittest
from unittest.mock import patch
from config.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Sauvegarder les variables d'environnement existantes
        self.original_env = dict(os.environ)
        
        # Créer un fichier de configuration de test
        self.test_config_path = 'test_config.yaml'
        with open(self.test_config_path, 'w') as f:
            f.write("""
polyad:
  debug: true
  log_level: DEBUG
  model:
    name: "test-model"
    temperature: 0.7
    max_tokens: 2048
  memory:
    quantization: q4_0
    embedding_compression: true
    cache_size: 2GB
  performance:
    batch_size: 16
    parallel_workers: 4
    max_queue_size: 100
  redis:
    host: localhost
    port: 6379
    db: 0
    password: ""
  ollama:
    host: localhost
    port: 11434
    api_key: ""
  prometheus:
    port: 9090
  grafana:
    port: 3000
    admin_user: admin
    admin_password: admin
  monitoring:
    interval: 5
    log_file_path: ./logs/polyad.log
  api_keys:
    HUGGINGFACE_API_KEY: "test-key"
""")

    def tearDown(self):
        # Restaurer les variables d'environnement
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Supprimer le fichier de test
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_load_config(self):
        """Test du chargement de la configuration."""
        config = Config(self.test_config_path)
        self.assertTrue(config.get_config()['debug'])
        self.assertEqual(config.get_config()['log_level'], 'DEBUG')
        self.assertEqual(config.get_model_config()['name'], 'test-model')

    def test_environment_override(self):
        """Test de la priorité des variables d'environnement."""
        os.environ['DEBUG'] = 'false'
        os.environ['MODEL_NAME'] = 'env-model'
        os.environ['HUGGINGFACE_API_KEY'] = 'env-key'
        
        config = Config(self.test_config_path)
        self.assertFalse(config.get_config()['debug'])
        self.assertEqual(config.get_model_config()['name'], 'env-model')
        self.assertEqual(config.get_api_keys()['HUGGINGFACE_API_KEY'], 'env-key')

    def test_invalid_config_file(self):
        """Test du chargement d'un fichier de configuration invalide."""
        with open('invalid_config.yaml', 'w') as f:
            f.write("invalid yaml")
        
        config = Config('invalid_config.yaml')
        self.assertFalse(config.get_config()['debug'])  # Utilise les valeurs par défaut
        
        if os.path.exists('invalid_config.yaml'):
            os.remove('invalid_config.yaml')

if __name__ == '__main__':
    unittest.main()
