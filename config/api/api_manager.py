import os
import json
from typing import Dict, Any
from pathlib import Path
import logging
from .logging_config import get_logger

def load_apis() -> Dict[str, Any]:
    """Charge la configuration des APIs depuis le fichier JSON."""
    logger = get_logger('api.api_manager')
    
    try:
        # Obtenir le chemin du fichier de configuration
        config_path = Path(os.path.dirname(__file__)) / 'apis.json'
        logger.info(f"Chargement de la configuration des APIs depuis {config_path}")
        
        # Charger le fichier de configuration
        if config_path.exists():
            with open(config_path, 'r') as f:
                apis_config = json.load(f)
                logger.debug(f"Configuration chargée: {apis_config}")
        else:
            logger.warning("Fichier de configuration non trouvé, utilisation de la configuration par défaut")
            # Configuration par défaut si le fichier n'existe pas
            apis_config = {
                "version": "2.0.0",
                "apis": {
                    "huggingface": {
                        "enabled": True,
                        "api_key": "",
                        "base_url": "https://api-inference.huggingface.co/models/",
                        "rate_limit": 100,
                        "cache_ttl": 3600
                    },
                    "wikipedia": {
                        "enabled": True,
                        "api_key": "",
                        "base_url": "https://en.wikipedia.org/w/api.php",
                        "rate_limit": 200,
                        "cache_ttl": 7200
                    }
                }
            }
            logger.debug(f"Configuration par défaut: {apis_config}")
            
        # Mettre à jour les clés API depuis les variables d'environnement
        for api_name, api_config in apis_config['apis'].items():
            # Obtenir le nom de la variable d'environnement correspondante
            env_key = f"{api_name.upper()}_API_KEY"
            logger.debug(f"Vérification de la variable d'environnement {env_key}")
            
            # Mettre à jour la clé API si elle existe dans les variables d'environnement
            if env_key in os.environ:
                api_config['api_key'] = os.environ[env_key]
                logger.info(f"Clé API mise à jour pour {api_name}")
            else:
                logger.debug(f"Variable d'environnement {env_key} non trouvée")
        
        logger.info("Configuration des APIs chargée avec succès")
        return apis_config
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des APIs: {e}", exc_info=True)
        return {
            "version": "2.0.0",
            "apis": {
                "huggingface": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://api-inference.huggingface.co/models/",
                    "rate_limit": 100,
                    "cache_ttl": 3600
                },
                "wikipedia": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://en.wikipedia.org/w/api.php",
                    "rate_limit": 200,
                    "cache_ttl": 7200
                }
            }
        }
