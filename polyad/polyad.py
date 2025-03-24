from polyad.core.agent import PolyadAgent
from polyad.core.memory import MemoryManager
from polyad.core.model import ModelManager
from polyad.core.api import APIManager
from polyad.core.utils import get_logger
import os

class Polyad:
    def __init__(self):
        """Initialise l'application Polyad."""
        self.logger = get_logger(__name__)
        self.logger.info("Initialisation de Polyad")
        
        # Initialiser les composants
        self.agent = PolyadAgent()
        self.memory = MemoryManager()
        self.model = ModelManager()
        self.api = APIManager()
        
        # Charger la configuration
        self.load_config()
        
    def load_config(self):
        """Charge la configuration de l'application."""
        # Charger les variables d'environnement
        self.config = {
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD', '')
            },
            'ollama': {
                'host': os.getenv('OLLAMA_HOST', 'localhost'),
                'port': int(os.getenv('OLLAMA_PORT', '11434')),
                'api_key': os.getenv('OLLAMA_API_KEY', '')
            },
            'model': {
                'name': os.getenv('MODEL_NAME', 'gemma3:12b-it-q4_K_M'),
                'temperature': float(os.getenv('TEMPERATURE', '0.7')),
                'max_tokens': int(os.getenv('MAX_TOKENS', '2048'))
            },
            'memory': {
                'quantization': os.getenv('MEMORY_QUANTIZATION', 'q4_0'),
                'embedding_compression': os.getenv('MEMORY_EMBEDDING_COMPRESSION', 'True').lower() == 'true',
                'cache_size': os.getenv('CACHE_SIZE', '2GB')
            },
            'monitoring': {
                'interval': int(os.getenv('MONITORING_INTERVAL', '5')),
                'log_file': os.getenv('LOG_FILE_PATH', './logs/polyad.log')
            },
            'performance': {
                'batch_size': int(os.getenv('BATCH_SIZE', '8')),
                'parallel_workers': int(os.getenv('PARALLEL_WORKERS', '4')),
                'max_queue_size': int(os.getenv('MAX_QUEUE_SIZE', '100'))
            }
        }
        
        self.logger.info("Configuration chargée avec succès")
        
    def start(self):
        """Démarre l'application."""
        self.logger.info("Démarrage de Polyad")
        
        try:
            # Initialiser les composants
            self.agent.initialize()
            self.memory.initialize()
            self.model.initialize()
            self.api.initialize()
            
            self.logger.info("Polyad démarré avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage: {str(e)}")
            raise

if __name__ == '__main__':
    app = Polyad()
    app.start()
