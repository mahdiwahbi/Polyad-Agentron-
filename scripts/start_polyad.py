import os
import sys
import subprocess
import logging

# Ajouter le répertoire parent au PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.api.api_manager import load_apis
from config.environments import load_environment

def start_polyad():
    """Démarre l'application Polyad."""
    setup_logging()
    logger = logging.getLogger('polyad.app')
    
    try:
        # Vérifier que le dossier de l'application existe
        app_dir = os.path.join(os.path.dirname(__file__), '..')
        if not os.path.exists(app_dir):
            logger.error(f"Le dossier de l'application n'existe pas: {app_dir}")
            raise FileNotFoundError(f"Le dossier de l'application n'existe pas: {app_dir}")
        
        # Changer le répertoire de travail
        os.chdir(app_dir)
        
        # Démarrer l'application
        subprocess.run([sys.executable, "-m", "streamlit", "run", "polyad_app.py"])
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'application: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    start_polyad()
