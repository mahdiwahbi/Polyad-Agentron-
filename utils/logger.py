import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

class PolyadLogger:
    def __init__(self, log_dir: str = None):
        """
        Initialise le système de logging Polyad
        
        Args:
            log_dir: Répertoire des logs (optionnel)
        """
        # Configurer le répertoire de logs
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configurer le logger principal
        self.logger = logging.getLogger('polyad')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # File handler
        self.file_handler = logging.FileHandler(
            f"logs/polyad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self.file_handler.setLevel(logging.INFO)

        # Console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False
        
        # Statistiques de logging
        self.stats = {
            "info_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "start_time": datetime.now().isoformat()
        }
        
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log un message de niveau INFO"""
        self.stats["info_count"] += 1
        if extra:
            message = f"{message} | {json.dumps(extra)}"
        self.logger.info(message)
        
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log un message de niveau WARNING"""
        self.stats["warning_count"] += 1
        if extra:
            message = f"{message} | {json.dumps(extra)}"
        self.logger.warning(message)
        
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log un message de niveau ERROR"""
        self.stats["error_count"] += 1
        if extra:
            message = f"{message} | {json.dumps(extra)}"
        self.logger.error(message)
        
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de logging"""
        self.stats["end_time"] = datetime.now().isoformat()
        return self.stats
        
    def rotate_logs(self):
        """Rotation des fichiers de logs"""
        current_log = self.file_handler.baseFilename
        if os.path.exists(current_log):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_log = os.path.join(
                self.log_dir, 
                f'polyad_{timestamp}.log'
            )
            os.rename(current_log, archive_log)
            
            # Recréer les handlers
            self.logger.handlers = []
            self.file_handler = logging.FileHandler(current_log)
            self.file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(self.file_handler)
            self.logger.addHandler(self.console_handler)
            
    def cleanup_old_logs(self, max_age_days: int = 7):
        """Nettoie les vieux fichiers de logs"""
        current_time = datetime.now()
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log') and filename != 'polyad.log':
                filepath = os.path.join(self.log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if (current_time - file_time).days > max_age_days:
                    os.remove(filepath)
                    self.info(f"Suppression du vieux log: {filename}")

# Instance globale du logger
logger = PolyadLogger()