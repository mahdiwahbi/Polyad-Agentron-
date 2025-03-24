import logging
import os

def get_logger(name):
    """Configure et retourne un logger."""
    # Créer le dossier des logs s'il n'existe pas
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurer le logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Créer le handler pour les logs
    log_file = os.path.join(log_dir, 'api.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Créer le formatteur
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Ajouter le handler au logger
    logger.addHandler(file_handler)
    
    return logger
