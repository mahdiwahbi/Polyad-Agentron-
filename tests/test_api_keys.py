import os
import unittest
from unittest.mock import patch
from config.environments import load_environment

class TestAPIKeys(unittest.TestCase):
    def setUp(self):
        # Sauvegarder les variables d'environnement existantes
        self.original_env = dict(os.environ)
        
        # Définir des clés API de test
        self.test_keys = {
            'HUGGINGFACE_API_KEY': 'test-huggingface-key',
            'WIKIPEDIA_API_KEY': 'test-wikipedia-key',
            'OPENMETEO_API_KEY': 'test-openmeteo-key',
            'NEWSAPI_API_KEY': 'test-newsapi-key',
            'LIBRETRANSLATE_API_KEY': 'test-libretranslate-key',
            'OCR_SPACE_API_KEY': 'test-ocr-space-key',
            'MEANINGCLOUD_API_KEY': 'test-meaningcloud-key',
            'MEILISEARCH_API_KEY': 'test-meilisearch-key',
            'SLACK_API_KEY': 'test-slack-key',
            'GITHUB_API_KEY': 'test-github-key',
            'GOOGLE_CALENDAR_API_KEY': 'test-google-calendar-key',
            'NOTION_API_KEY': 'test-notion-key'
        }
        
        # Définir les variables d'environnement de test
        for key, value in self.test_keys.items():
            os.environ[key] = value

    def tearDown(self):
        # Restaurer les variables d'environnement
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_api_keys(self):
        """Test du chargement des clés API."""
        env = load_environment()
        api_keys = env['api_keys']
        
        # Vérifier que toutes les clés sont présentes
        for key in self.test_keys:
            key_lower = key.lower()
            if key_lower in api_keys:
                self.assertEqual(api_keys[key_lower], self.test_keys[key])
            else:
                # Pour les clés qui ne sont pas directement mappées
                key_mapped = key.replace('_', '').lower()
                self.assertEqual(api_keys[key_mapped], self.test_keys[key])

    def test_default_values(self):
        """Test des valeurs par défaut pour les clés API."""
        # Supprimer les variables d'environnement
        for key in self.test_keys:
            if key in os.environ:
                del os.environ[key]
        
        env = load_environment()
        api_keys = env['api_keys']
        
        # Vérifier que toutes les clés sont vides par défaut
        for key in api_keys:
            self.assertEqual(api_keys[key], '')

    def test_invalid_keys(self):
        """Test avec des clés API invalides."""
        # Définir des clés invalides
        os.environ['INVALID_API_KEY'] = 'invalid-key'
        os.environ['HUGGINGFACE_API_KEY'] = 'invalid-key'
        
        env = load_environment()
        api_keys = env['api_keys']
        
        # Vérifier que la clé invalide n'est pas dans la configuration
        self.assertNotIn('invalid_api_key', api_keys)
        
        # Vérifier que la clé HuggingFace est correctement mise en minuscules
        self.assertEqual(api_keys['huggingface_api_key'], 'invalid-key')

    def test_case_insensitive_keys(self):
        """Test de la gestion des clés API en majuscules/minuscules."""
        # Définir des clés avec différentes casse
        os.environ['HUGGINGFACE_API_KEY'] = 'upper-case-key'
        os.environ['huggingface_api_key'] = 'lower-case-key'
        
        env = load_environment()
        api_keys = env['api_keys']
        
        # Vérifier que la clé en minuscules a la priorité
        self.assertEqual(api_keys['huggingface_api_key'], 'lower-case-key')

if __name__ == '__main__':
    unittest.main()
