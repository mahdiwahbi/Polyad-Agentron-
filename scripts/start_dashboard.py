import os
import subprocess
import sys
import logging
from config.logging_config import setup_logging

def start_dashboard():
    """Démarre le dashboard."""
    setup_logging()
    logger = logging.getLogger('polyad.dashboard')
    
    try:
        # Vérifier que le dossier du dashboard existe
        dashboard_dir = os.path.join(os.path.dirname(__file__), '..', 'dashboard')
        if not os.path.exists(dashboard_dir):
            logger.error(f"Le dossier du dashboard n'existe pas: {dashboard_dir}")
            raise FileNotFoundError(f"Le dossier du dashboard n'existe pas: {dashboard_dir}")
        
        # Changer le répertoire de travail
        os.chdir(dashboard_dir)
        
        # Démarrer Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du dashboard: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    start_dashboard()
