import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from config.logging_config import setup_logging

def initialize_environment():
    """Initialise l'environnement de l'application."""
    # Configurer les logs
    setup_logging()
    logger = logging.getLogger('polyad.init')
    
    try:
        # Charger les variables d'environnement
        env_files = [
            ".env.local",  # Priorité la plus haute
            ".env",       # Priorité normale
            ".env.production"  # Priorité la plus basse
        ]
        
        for env_file in env_files:
            if Path(env_file).exists():
                logger.info(f"Chargement des variables d'environnement depuis {env_file}")
                load_dotenv(env_file, override=True)
        
        # Vérifier les variables d'environnement essentielles
        required_env_vars = [
            'POLYAD_DEBUG',
            'POLYAD_LOG_LEVEL',
            'REDIS_HOST',
            'OLLAMA_HOST',
            'POLYAD_MODEL'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if var not in os.environ:
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
            raise EnvironmentError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        
        # Créer les dossiers nécessaires
        required_dirs = [
            'logs',
            'data',
            'models',
            'cache'
        ]
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                logger.info(f"Création du dossier {dir_name}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Initialisation de l'environnement terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'environnement: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    initialize_environment()
