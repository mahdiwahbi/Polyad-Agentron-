"""
Gestionnaire centralisé des services Polyad
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from .config import Config

class ServiceManager:
    """Gestionnaire centralisé des services Polyad"""
    def __init__(self, config: Config):
        """Initialise le gestionnaire de services
        
        Args:
            config (Config): Configuration de l'application
        """
        self.config = config
        self.logger = logging.getLogger('polyad.service_manager')
        self._stop_requested = False
        self._services: Dict[str, Any] = {}
        
        # Charger la configuration des services
        self._load_services_config()
        
    def _load_services_config(self) -> None:
        """Charge la configuration des services"""
        try:
            services_config = self.config.get('services', {})
            ports_config = self.config.get('ports', {})
            
            for service_name, service_config in services_config.items():
                if not service_config.get('enabled', True):
                    continue
                    
                # Configurer les ports
                if service_name in ports_config:
                    service_config['port'] = ports_config[service_name]
                    
                self._services[service_name] = service_config
                
            self.logger.info("Configuration des services chargée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration des services: {e}")
            raise

    def start_service(self, service_name: str) -> bool:
        """Démarrer un service spécifique
        
        Args:
            service_name (str): Nom du service à démarrer
            
        Returns:
            bool: True si le service a été démarré avec succès, False sinon
        """
        if service_name not in self._services:
            self.logger.error(f"Service {service_name} non configuré")
            return False
            
        service_config = self._services[service_name]
        
        try:
            # Construire la commande de démarrage
            cmd = ["docker-compose", "up", "-d", service_config['name']]
            if 'env_file' in service_config:
                cmd.extend(["--env-file", service_config['env_file']])
                
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                check=True,
                capture_output=True,
                text=True
            )
            
            self.logger.info(f"Service {service_name} démarré avec succès")
            self.logger.debug(f"Commande exécutée: {cmd}")
            self.logger.debug(f"Sortie: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erreur lors du démarrage de {service_name}: {e}")
            self.logger.debug(f"Commande: {e.cmd}")
            self.logger.debug(f"Sortie: {e.output}")
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors du démarrage de {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Arrêter un service spécifique
        
        Args:
            service_name (str): Nom du service à arrêter
            
        Returns:
            bool: True si le service a été arrêté avec succès, False sinon
        """
        if service_name not in self._services:
            self.logger.error(f"Service {service_name} non configuré")
            return False
            
        service_config = self._services[service_name]
        
        try:
            # Construire la commande d'arrêt
            cmd = ["docker-compose", "stop", service_config['name']]
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                check=True,
                capture_output=True,
                text=True
            )
            
            self.logger.info(f"Service {service_name} arrêté avec succès")
            self.logger.debug(f"Commande exécutée: {cmd}")
            self.logger.debug(f"Sortie: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erreur lors de l'arrêt de {service_name}: {e}")
            self.logger.debug(f"Commande: {e.cmd}")
            self.logger.debug(f"Sortie: {e.output}")
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de l'arrêt de {service_name}: {e}")
            return False

    def start_all(self) -> bool:
        """Démarrer tous les services
        
        Returns:
            bool: True si tous les services ont été démarrés avec succès, False sinon
        """
        success = True
        
        for service_name in self._services:
            if not self.start_service(service_name):
                success = False
                
        return success

    def stop_all(self) -> bool:
        """Arrêter tous les services
        
        Returns:
            bool: True si tous les services ont été arrêtés avec succès, False sinon
        """
        success = True
        
        for service_name in self._services:
            if not self.stop_service(service_name):
                success = False
                
        return success

    def check_status(self, service_name: str) -> bool:
        """Vérifier le statut d'un service
        
        Args:
            service_name (str): Nom du service à vérifier
            
        Returns:
            bool: True si le service est en cours d'exécution, False sinon
        """
        if service_name not in self._services:
            return False
            
        service_config = self._services[service_name]
        
        try:
            # Vérifier le statut du container
            cmd = ["docker", "ps", "--filter", f"name={service_config['name']}", "--format", "{{.Status}}"]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            return "Up" in result.stdout
            
        except subprocess.CalledProcessError:
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du statut de {service_name}: {e}")
            return False

    def get_service_logs(self, service_name: str, tail: int = 100) -> Optional[str]:
        """Obtenir les logs d'un service
        
        Args:
            service_name (str): Nom du service
            tail (int): Nombre de lignes à afficher
            
        Returns:
            Optional[str]: Logs du service ou None en cas d'erreur
        """
        if service_name not in self._services:
            return None
            
        service_config = self._services[service_name]
        
        try:
            cmd = ["docker-compose", "logs", "--tail", str(tail), service_config['name']]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erreur lors de la récupération des logs de {service_name}: {e}")
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la récupération des logs de {service_name}: {e}")
            return None
