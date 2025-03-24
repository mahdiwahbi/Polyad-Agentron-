import os
from pathlib import Path
import json
from dotenv import load_dotenv
from typing import Dict, Any

# Charger les variables d'environnement
def load_environment():
    """Charger les variables d'environnement depuis les fichiers .env"""
    env_files = [
        Path('.env.local'),  # Priorité 1
        Path('.env'),       # Priorité 2
        Path('.env.production')  # Priorité 3
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file)
            break

# Configuration de base
class Config:
    def __init__(self):
        load_environment()
        
        # Chemins
        self.APP_DIR = Path(__file__).parent
        self.DOCKER_COMPOSE_PATH = self.APP_DIR / "docker-compose.yml"
        self.ENV_FILE_PATH = self.APP_DIR / ".env"
        
        # Ports
        self.SERVICE_PORTS = {
            "API": int(os.getenv('API_PORT', '8000')),
            "Dashboard": int(os.getenv('DASHBOARD_PORT', '8001')),
            "Prometheus": int(os.getenv('PROMETHEUS_PORT', '9090')),
            "Grafana": int(os.getenv('GRAFANA_PORT', '3000'))
        }
        
        # Configuration Docker
        self.DOCKER_CONFIG = {
            "image": os.getenv('DOCKER_IMAGE', 'polyad/app:latest'),
            "network": os.getenv('DOCKER_NETWORK', 'polyad_network')
        }
        
        # Configuration API
        self.API_CONFIG = {
            "host": os.getenv('API_HOST', '0.0.0.0'),
            "port": self.SERVICE_PORTS["API"],
            "debug": os.getenv('API_DEBUG', 'false').lower() == 'true'
        }
        
        # Configuration Monitoring
        self.MONITORING_CONFIG = {
            "prometheus": {
                "enabled": os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true',
                "port": self.SERVICE_PORTS["Prometheus"]
            },
            "grafana": {
                "enabled": os.getenv('GRAFANA_ENABLED', 'true').lower() == 'true',
                "port": self.SERVICE_PORTS["Grafana"]
            }
        }
        
        # Base paths
        self.BASE_DIR = Path(os.path.expanduser("~/Desktop/polyad"))
        self.CACHE_DIR = self.BASE_DIR / "cache"
        self.DATA_DIR = self.BASE_DIR / "data"

        # Model configs
        self.MODEL_CONFIGS = {
            "high_ram": {
                "name": "gemma3:12b-q4_0",
                "min_ram": 10  # GB
            },
            "low_ram": {
                "name": "gemma3:12b-q2_K",
                "min_ram": 6  # GB
            }
        }

        # Configuration système
        self.RESOURCE_CONFIG = {
            "cpu_threshold": 80,      # Seuil d'utilisation CPU en %
            "gpu_threshold": 70,      # Seuil d'utilisation GPU en %
            "thermal_threshold": 85,   # Seuil de température en °C
            "memory_threshold": 0.8    # Seuil d'utilisation mémoire (0-1)
        }

        self.MEMORY_CONFIG = {
            "quantization_level": "q4_0",  # Niveau de quantification
            "embedding_compression": True, # Compression des embeddings
            "cache_size": 2 * 1024 * 1024 * 1024,  # 2 Go
            "eviction_strategy": "LRU"     # Stratégie d'élimination du cache
        }

        self.VECTOR_STORE_CONFIG = {
            "type": "faiss",             # Type de stockage vectoriel
            "implementation": "cpu",     # Utilisation de CPU
            "dimension": 768,           # Dimension des vecteurs
            "index_type": "IndexFlatL2"  # Type d'index
        }

        self.MODEL_CONFIG = {
            "name": "gemma3:12b-it-q4_K_M",  # Nom du modèle
            "temperature": 0.7,               # Température
            "max_tokens": 2048,              # Nombre maximum de tokens
            "top_p": 0.95,                   # Top-p sampling
            "top_k": 50,                     # Top-k sampling
            "repetition_penalty": 1.1,       # Pénalité de répétition
            "context_window": 4096           # Taille de la fenêtre contextuelle
        }

        self.MONITORING_CONFIG = {
            "interval": 5,                 # Intervalle de surveillance en secondes
            "prometheus_port": 9090,       # Port Prometheus
            "grafana_port": 3000,          # Port Grafana
            "log_level": "INFO",           # Niveau de log
            "metrics": {
                "cpu": True,               # Surveillance CPU
                "gpu": True,               # Surveillance GPU
                "memory": True,            # Surveillance mémoire
                "disk": True,              # Surveillance disque
                "network": True            # Surveillance réseau
            }
        }

        self.PERFORMANCE_CONFIG = {
            "text_generation": {
                "batch_size": 8,           # Taille de batch
                "parallel_workers": 4,     # Nombre de workers parallèles
                "max_queue_size": 100      # Taille maximale de la file d'attente
            },
            "vision": {
                "frame_rate": 30,          # Fréquence d'images
                "resolution": "1920x1080", # Résolution
                "compression": "h264"      # Algorithme de compression
            },
            "audio": {
                "sample_rate": 44100,      # Taux d'échantillonnage
                "channels": 2,            # Nombre de canaux
                "format": "wav"           # Format audio
            }
        }

        self.CACHE_CONFIG = {
            "type": "redis",              # Type de cache
            "ttl": 3600,                 # TTL en secondes (1 heure)
            "max_size": 2 * 1024 * 1024 * 1024,  # 2 Go
            "eviction_strategy": "LRU",   # Stratégie d'élimination
            "compression": True,          # Compression activée
            "compression_level": 9        # Niveau de compression
        }

        # Configuration des services
        self.SERVICE_CONFIG: Dict[str, Any] = {
            "ollama": {
                "host": "http://localhost:11434",
                "timeout": 30,
                "retry_attempts": 3
            },
            "cache": {
                "type": "redis",
                "ttl": 3600,  # 1 heure
                "max_size": 4 * 1024 * 1024 * 1024  # 4 Go
            }
        }

    def get_service_url(self, service_name):
        """Obtenir l'URL d'un service"""
        if service_name not in self.SERVICE_PORTS:
            raise ValueError(f"Service {service_name} non défini")
            
        return f"http://localhost:{self.SERVICE_PORTS[service_name]}"

# Instance unique de la configuration
config = Config()
