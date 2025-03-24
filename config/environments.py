import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

def load_environment() -> Dict[str, Any]:
    """Charge les variables d'environnement depuis les fichiers .env."""
    # Liste des fichiers .env par ordre de priorité
    env_files = [
        ".env.local",  # Priorité la plus haute
        ".env",       # Priorité normale
        ".env.production"  # Priorité la plus basse
    ]
    
    # Configuration par défaut
    env_vars = {
        "debug": False,
        "log_level": "INFO",
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": ""
        },
        "ollama": {
            "host": "localhost",
            "port": 11434,
            "api_key": ""
        },
        "prometheus": {
            "port": 9090
        },
        "grafana": {
            "port": 3000,
            "admin_user": "admin",
            "admin_password": "admin"
        },
        "model": {
            "name": "gemma3:12b-it-q4_K_M",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "memory": {
            "quantization": "q4_0",
            "embedding_compression": True,
            "cache_size": "2GB"
        },
        "monitoring": {
            "interval": 5,
            "log_file_path": "./logs/polyad.log"
        },
        "performance": {
            "batch_size": 8,
            "parallel_workers": 4,
            "max_queue_size": 100
        },
        "api_keys": {
            "HUGGINGFACE_API_KEY": "",
            "WIKIPEDIA_API_KEY": "",
            "OPENMETEO_API_KEY": "",
            "NEWSAPI_API_KEY": "",
            "LIBRETRANSLATE_API_KEY": "",
            "OCR_SPACE_API_KEY": "",
            "MEANINGCLOUD_API_KEY": "",
            "MEILISEARCH_API_KEY": "",
            "SLACK_API_KEY": "",
            "GITHUB_API_KEY": "",
            "GOOGLE_CALENDAR_API_KEY": "",
            "NOTION_API_KEY": ""
        }
    }
    
    # Charger les fichiers .env et mettre à jour la configuration
    for env_file in env_files:
        if Path(env_file).exists():
            load_dotenv(env_file, override=True)
            
            # Mettre à jour les variables booléennes
            env_vars['debug'] = os.getenv("DEBUG", "false").lower() == "true"
            
            # Mettre à jour les configurations spécifiques
            env_vars['redis'].update({
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "0")),
                "password": os.getenv("REDIS_PASSWORD", "")
            })
            
            env_vars['ollama'].update({
                "host": os.getenv("OLLAMA_HOST", "localhost"),
                "port": int(os.getenv("OLLAMA_PORT", "11434")),
                "api_key": os.getenv("OLLAMA_API_KEY", "")
            })
            
            env_vars['prometheus']['port'] = int(os.getenv("PROMETHEUS_PORT", "9090"))
            env_vars['grafana'].update({
                "port": int(os.getenv("GRAFANA_PORT", "3000")),
                "admin_user": os.getenv("GRAFANA_ADMIN_USER", "admin"),
                "admin_password": os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
            })
            
            env_vars['model'].update({
                "name": os.getenv("MODEL_NAME", "gemma3:12b-it-q4_K_M"),
                "temperature": float(os.getenv("TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("MAX_TOKENS", "2048"))
            })
            
            env_vars['memory'].update({
                "quantization": os.getenv("MEMORY_QUANTIZATION", "q4_0"),
                "embedding_compression": os.getenv("MEMORY_EMBEDDING_COMPRESSION", "true").lower() == "true",
                "cache_size": os.getenv("CACHE_SIZE", "2GB")
            })
            
            env_vars['monitoring'].update({
                "interval": int(os.getenv("MONITORING_INTERVAL", "5")),
                "log_file_path": os.getenv("LOG_FILE_PATH", "./logs/polyad.log")
            })
            
            env_vars['performance'].update({
                "batch_size": int(os.getenv("BATCH_SIZE", "8")),
                "parallel_workers": int(os.getenv("PARALLEL_WORKERS", "4")),
                "max_queue_size": int(os.getenv("MAX_QUEUE_SIZE", "100"))
            })
            
            # Mettre à jour les clés API
            for key in env_vars['api_keys']:
                env_key = key.replace('_', '').upper()
                env_vars['api_keys'][key] = os.getenv(env_key, "")
    
    return env_vars