import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(os.path.expanduser("~/Desktop/polyad"))
CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"

# Model configs
MODEL_CONFIGS = {
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
RESOURCE_CONFIG = {
    "cpu_threshold": 80,      # Seuil d'utilisation CPU en %
    "gpu_threshold": 70,      # Seuil d'utilisation GPU en %
    "thermal_threshold": 85,   # Seuil de température en °C
    "memory_threshold": 0.8    # Seuil d'utilisation mémoire (0-1)
}

MEMORY_CONFIG = {
    "quantization_level": "q4_0",  # Niveau de quantification
    "embedding_compression": True, # Compression des embeddings
    "cache_size": 2 * 1024 * 1024 * 1024,  # 2 Go
    "eviction_strategy": "LRU"     # Stratégie d'élimination du cache
}

VECTOR_STORE_CONFIG = {
    "type": "faiss",             # Type de stockage vectoriel
    "implementation": "cpu",     # Utilisation de CPU
    "dimension": 768,           # Dimension des vecteurs
    "index_type": "IndexFlatL2"  # Type d'index
}

MODEL_CONFIG = {
    "name": "gemma3:12b-it-q4_K_M",  # Nom du modèle
    "temperature": 0.7,               # Température
    "max_tokens": 2048,              # Nombre maximum de tokens
    "top_p": 0.95,                   # Top-p sampling
    "top_k": 50,                     # Top-k sampling
    "repetition_penalty": 1.1,       # Pénalité de répétition
    "context_window": 4096           # Taille de la fenêtre contextuelle
}

MONITORING_CONFIG = {
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

PERFORMANCE_CONFIG = {
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

CACHE_CONFIG = {
    "type": "redis",              # Type de cache
    "ttl": 3600,                 # TTL en secondes (1 heure)
    "max_size": 2 * 1024 * 1024 * 1024,  # 2 Go
    "eviction_strategy": "LRU",   # Stratégie d'élimination
    "compression": True,          # Compression activée
    "compression_level": 9        # Niveau de compression
}

# Configuration des services
SERVICE_CONFIG: Dict[str, Any] = {
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
