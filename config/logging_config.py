import logging
import os
from pathlib import Path

def setup_logging():
    """Configure le système de logging."""
    # Créer le dossier des logs s'il n'existe pas
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Configuration de base
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/polyad.log'),
            logging.StreamHandler()
        ]
    )

    # Configuration spécifique pour les modules
    logging.getLogger('polyad').setLevel(logging.DEBUG)
    logging.getLogger('config').setLevel(logging.INFO)
    logging.getLogger('api').setLevel(logging.INFO)
    logging.getLogger('monitoring').setLevel(logging.WARN)

    # Réduire le niveau de log pour les dépendances externes
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    # Ajouter des formateurs spécifiques
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configurer le logger pour les APIs
    api_logger = logging.getLogger('api')
    api_file_handler = logging.FileHandler('logs/api.log')
    api_file_handler.setFormatter(formatter)
    api_logger.addHandler(api_file_handler)
    
    # Configurer le logger pour la surveillance
    monitoring_logger = logging.getLogger('monitoring')
    monitoring_file_handler = logging.FileHandler('logs/monitoring.log')
    monitoring_file_handler.setFormatter(formatter)
    monitoring_logger.addHandler(monitoring_file_handler)

    # Configurer le logger pour les erreurs
    error_logger = logging.getLogger('error')
    error_file_handler = logging.FileHandler('logs/error.log')
    error_file_handler.setFormatter(formatter)
    error_logger.addHandler(error_file_handler)
    error_logger.setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    """Crée un logger avec le nom spécifié."""
    return logging.getLogger(name)

# Initialiser la configuration des logs
setup_logging()
