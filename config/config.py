from typing import Dict, Any
import os
import logging
from pathlib import Path
import yaml

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
        """Charge la configuration depuis le fichier"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                self.logger.warning(f"Fichier de configuration non trouvé: {config_path}")
                self._create_default_config()
                return
                
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                
            self.logger.info("Configuration chargée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            raise

    def _create_default_config(self) -> None:
        """Crée une configuration par défaut"""
        self.config = {
            # Configuration générale
            'debug': False,
            'log_level': 'INFO',
            
            # Configuration du cache
            'cache': {
                'size': 1024 * 1024 * 1024,  # 1GB
                'ttl': 3600,  # 1 heure
                'cleanup_interval': 300,  # 5 minutes
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0
                }
            },
            
            # Configuration GPU
            'gpu': {
                'memory_threshold': 0.8,
                'temperature_threshold': 80,
                'optimization_interval': 60  # secondes
            },
            
            # Configuration de sécurité
            'security': {
                'encryption_key': None,
                'salt': None,
                'iterations': 100000
            },
            
            # Configuration de monitoring
            'monitoring': {
                'grafana': {
                    'api_key': None,
                    'host': 'localhost',
                    'port': 3000
                },
                'metrics_interval': 1,  # seconde
                'alert_thresholds': {
                    'cpu': 90,
                    'memory': 90,
                    'temperature': 80
                }
            }
        }
        
        self._save_config()
        self.logger.info("Configuration par défaut créée")

    def _save_config(self) -> None:
        """Sauvegarde la configuration"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f)
            self.logger.info("Configuration sauvegardée")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            raise

    def _validate_config(self) -> None:
        """Valide la configuration"""
        required_fields = [
            'cache',
            'gpu',
            'security',
            'monitoring'
        ]
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Configuration manquante: {field}")
                
        # Valider les valeurs
        if self.config['cache']['size'] <= 0:
            raise ValueError("Taille du cache invalide")
            
        if self.config['cache']['ttl'] <= 0:
            raise ValueError("TTL du cache invalide")
            
        if self.config['gpu']['memory_threshold'] < 0 or self.config['gpu']['memory_threshold'] > 1:
            raise ValueError("Seuil mémoire GPU invalide")
            
        if self.config['gpu']['temperature_threshold'] < 0:
            raise ValueError("Seuil température GPU invalide")
            
        self.logger.info("Configuration validée")

    def get(self, key: str) -> Any:
        """Obtient une valeur de configuration
        
        Args:
            key (str): Clé de configuration
            
        Returns:
            Any: Valeur de configuration
        """
        return self.config.get(key)

    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration
        
        Args:
            key (str): Clé de configuration
            value (Any): Nouvelle valeur
        """
        self.config[key] = value
        self._save_config()

    def update(self, updates: Dict[str, Any]) -> None:
        """Met à jour la configuration
        
        Args:
            updates (Dict[str, Any]): Mises à jour de configuration
        """
        self.config.update(updates)
        self._save_config()

    def reload(self) -> None:
        """Recharge la configuration"""
        self._load_config()
        self._validate_config()

    def get_all(self) -> Dict[str, Any]:
        """Obtient toute la configuration
        
        Returns:
            Dict[str, Any]: Configuration complète
        """
        return self.config.copy()
