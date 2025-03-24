import os
import logging
from pathlib import Path
from config.logging_config import setup_logging

def initialize_logs():
    """Initialise le système de logging."""
    # Configurer les logs
    setup_logging()
    logger = logging.getLogger('polyad.init_logs')
    
    try:
        # Créer le dossier des logs s'il n'existe pas
        log_dir = Path('logs')
        if not log_dir.exists():
            logger.info("Création du dossier des logs")
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Vérifier les fichiers de log
        required_log_files = [
            'polyad.log',
            'api.log',
            'monitoring.log',
            'error.log'
        ]
        
        for log_file in required_log_files:
            log_path = log_dir / log_file
            if not log_path.exists():
                logger.info(f"Création du fichier de log {log_file}")
                log_path.touch()
        
        logger.info("Initialisation des logs terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des logs: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    initialize_logs()
