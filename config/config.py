from typing import Dict, Any
import os
import logging
from pathlib import Path
import yaml
import dotenv
from dotenv import load_dotenv
from .environments import load_environment
from .logging_config import setup_logging

class Config:
    def __init__(self, config_file: str = "config.yaml"):
        """Initialise la configuration
        
        Args:
            config_file (str): Chemin du fichier de configuration
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger('polyad.config')
        
        # Charger la configuration
        self._load_config()
        
        # Valider la configuration
        self._validate_config()

    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier et les variables d'environnement."""
        try:
            # Charger les variables d'environnement
            env_vars = load_environment()
            
            # Charger le fichier de configuration
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if isinstance(file_config, str):
                        file_config = {'polyad': {'debug': True}}  # Configuration par défaut si le fichier est invalide
            else:
                file_config = {'polyad': {}}
            
            # Fusionner la configuration du fichier avec les variables d'environnement
            self.config = {
                **env_vars,
                **file_config.get('polyad', {})
            }
            
            self.logger.info("Configuration chargée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            raise

    def _validate_config(self) -> None:
        """Valide la configuration."""
        required_keys = [
            'debug',
            'log_level',
            'redis',
            'ollama',
            'prometheus',
            'grafana',
            'model',
            'memory',
            'monitoring',
            'performance',
            'api_keys'
        ]
    
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValueError(f"Configuration manquante pour les clés: {', '.join(missing_keys)}")

    def get_config(self) -> Dict[str, Any]:
        """Retourne la configuration complète."""
        return self.config

    def get_api_keys(self) -> Dict[str, str]:
        """Retourne les clés API."""
        return self.config.get('api_keys', {})

    def get_model_config(self) -> Dict[str, Any]:
        """Retourne la configuration du modèle."""
        return self.config.get('model', {})

    def get_performance_config(self) -> Dict[str, Any]:
        """Retourne la configuration de performance."""
        return self.config.get('performance', {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Retourne la configuration de surveillance."""
        return self.config.get('monitoring', {})

    def get_memory_config(self) -> Dict[str, Any]:
        """Retourne la configuration de la mémoire."""
        return self.config.get('memory', {})

    def get_redis_config(self) -> Dict[str, Any]:
        """Retourne la configuration Redis."""
        return self.config.get('redis', {})

    def get_ollama_config(self) -> Dict[str, Any]:
        """Retourne la configuration Ollama."""
        return self.config.get('ollama', {})

    def get_prometheus_config(self) -> Dict[str, Any]:
        """Retourne la configuration Prometheus."""
        return self.config.get('prometheus', {})

    def get_grafana_config(self) -> Dict[str, Any]:
        """Retourne la configuration Grafana."""
        return self.config.get('grafana', {})

# Initialiser la configuration
global_config = Config()

# Initialiser la configuration des logs
setup_logging()
