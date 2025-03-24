import os
import unittest
from unittest.mock import patch, MagicMock
from config.api.api_manager import load_apis
import json

class TestAPIs(unittest.TestCase):
    def setUp(self):
        # Sauvegarder les variables d'environnement existantes
        self.original_env = dict(os.environ)
        
        # Créer un fichier de configuration de test
        self.test_config_path = 'test_apis.json'
        with open(self.test_config_path, 'w') as f:
            json.dump({
                "version": "2.0.0",
                "apis": {
                    "huggingface": {
                        "enabled": True,
                        "api_key": "test-huggingface-key",
                        "base_url": "https://api-inference.huggingface.co/models/",
                        "rate_limit": 100,
                        "cache_ttl": 3600
                    },
                    "wikipedia": {
                        "enabled": True,
                        "api_key": "test-wikipedia-key",
                        "base_url": "https://en.wikipedia.org/w/api.php",
                        "rate_limit": 200,
                        "cache_ttl": 7200
                    }
                }
            }, f)

    def tearDown(self):
        # Restaurer les variables d'environnement
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Supprimer le fichier de test
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_load_apis(self):
        """Test du chargement des configurations API."""
        with patch('os.path.dirname', return_value=os.path.dirname(self.test_config_path)):
            apis = load_apis()
            
            # Vérifier la structure de base
            self.assertIn('version', apis)
            self.assertIn('apis', apis)
            
            # Vérifier les configurations individuelles
            huggingface = apis['apis']['huggingface']
            self.assertTrue(huggingface['enabled'])
            self.assertEqual(huggingface['api_key'], 'test-huggingface-key')
            self.assertEqual(huggingface['base_url'], 'https://api-inference.huggingface.co/models/')
            self.assertEqual(huggingface['rate_limit'], 100)
            self.assertEqual(huggingface['cache_ttl'], 3600)
            
            wikipedia = apis['apis']['wikipedia']
            self.assertTrue(wikipedia['enabled'])
            self.assertEqual(wikipedia['api_key'], 'test-wikipedia-key')
            self.assertEqual(wikipedia['base_url'], 'https://en.wikipedia.org/w/api.php')
            self.assertEqual(wikipedia['rate_limit'], 200)
            self.assertEqual(wikipedia['cache_ttl'], 7200)

    def test_invalid_config(self):
        """Test du chargement d'une configuration API invalide."""
        # Créer un fichier de configuration invalide
        with open('invalid_apis.json', 'w') as f:
            f.write('invalid json')
            
        with patch('os.path.dirname', return_value=os.path.dirname('invalid_apis.json')):
            apis = load_apis()
            
            # Vérifier que la configuration par défaut est utilisée
            self.assertIn('version', apis)
            self.assertIn('apis', apis)
            
            # Vérifier que les clés API sont vides
            for api in apis['apis'].values():
                self.assertEqual(api['api_key'], '')
            
        if os.path.exists('invalid_apis.json'):
            os.remove('invalid_apis.json')

    def test_missing_api_key(self):
        """Test du chargement d'une configuration API sans clé API."""
        # Créer un fichier de configuration sans clé API
        with open('no_key_apis.json', 'w') as f:
            json.dump({
                "version": "2.0.0",
                "apis": {
                    "huggingface": {
                        "enabled": True,
                        "base_url": "https://api-inference.huggingface.co/models/",
                        "rate_limit": 100,
                        "cache_ttl": 3600
                    }
                }
            }, f)
            
        with patch('os.path.dirname', return_value=os.path.dirname('no_key_apis.json')):
            apis = load_apis()
            
            # Vérifier que la clé API est vide
            huggingface = apis['apis']['huggingface']
            self.assertEqual(huggingface['api_key'], '')
            
        if os.path.exists('no_key_apis.json'):
            os.remove('no_key_apis.json')

    def test_disabled_api(self):
        """Test du chargement d'une configuration API désactivée."""
        # Créer un fichier de configuration avec une API désactivée
        with open('disabled_apis.json', 'w') as f:
            json.dump({
                "version": "2.0.0",
                "apis": {
                    "huggingface": {
                        "enabled": False,
                        "api_key": "test-key",
                        "base_url": "https://api-inference.huggingface.co/models/",
                        "rate_limit": 100,
                        "cache_ttl": 3600
                    }
                }
            }, f)
            
        with patch('os.path.dirname', return_value=os.path.dirname('disabled_apis.json')):
            apis = load_apis()
            
            # Vérifier que l'API est désactivée
            huggingface = apis['apis']['huggingface']
            self.assertFalse(huggingface['enabled'])
            
        if os.path.exists('disabled_apis.json'):
            os.remove('disabled_apis.json')

if __name__ == '__main__':
    unittest.main()
