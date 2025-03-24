import os
import unittest
from config.environments import load_environment

class TestEnvironments(unittest.TestCase):
    def setUp(self):
        # Sauvegarder les variables d'environnement existantes
        self.original_env = dict(os.environ)
        
        # Définir des variables d'environnement de test
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['REDIS_HOST'] = 'test-redis'
        os.environ['OLLAMA_HOST'] = 'test-ollama'
        os.environ['MODEL_NAME'] = 'test-model'
        os.environ['MEMORY_QUANTIZATION'] = 'q4_1'
        os.environ['BATCH_SIZE'] = '16'
        os.environ['HUGGINGFACE_API_KEY'] = 'test-key'

    def tearDown(self):
        # Restaurer les variables d'environnement
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_environment(self):
        """Test du chargement des variables d'environnement."""
        env = load_environment()
        
        self.assertTrue(env['debug'])
        self.assertEqual(env['log_level'], 'DEBUG')
        self.assertEqual(env['redis']['host'], 'test-redis')
        self.assertEqual(env['ollama']['host'], 'test-ollama')
        self.assertEqual(env['model']['name'], 'test-model')
        self.assertEqual(env['memory']['quantization'], 'q4_1')
        self.assertEqual(env['performance']['batch_size'], 16)
        self.assertEqual(env['api_keys']['HUGGINGFACE_API_KEY'], 'test-key')

    def test_default_values(self):
        """Test des valeurs par défaut."""
        # Supprimer les variables d'environnement
        for key in ['DEBUG', 'LOG_LEVEL', 'REDIS_HOST', 'OLLAMA_HOST', 'MODEL_NAME']:
            if key in os.environ:
                del os.environ[key]
        
        env = load_environment()
        
        self.assertFalse(env['debug'])
        self.assertEqual(env['log_level'], 'INFO')
        self.assertEqual(env['redis']['host'], 'localhost')
        self.assertEqual(env['ollama']['host'], 'localhost')
        self.assertEqual(env['model']['name'], 'gemma3:12b-it-q4_K_M')
        self.assertEqual(env['memory']['quantization'], 'q4_0')
        self.assertEqual(env['performance']['batch_size'], 8)
        self.assertEqual(env['api_keys']['HUGGINGFACE_API_KEY'], '')

if __name__ == '__main__':
    unittest.main()
