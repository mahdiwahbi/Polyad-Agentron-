import psutil
import subprocess
import time
import asyncio
import logging
from typing import Dict, Any, Optional
import json

class SystemMonitor:
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialise le système de surveillance"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration des seuils de sécurité
        self.safety_limits = {
            'cpu': {
                'max_usage': 25,               # 25% maximum
                'warning_threshold': 20,       # 20% warning
                'critical_threshold': 15       # 15% critical
            },
            'memory': {
                'min_available': 4 * (1024 ** 3),  # 4Go minimum
                'warning_threshold': 3 * (1024 ** 3),  # 3Go warning
                'critical_threshold': 2 * (1024 ** 3)  # 2Go critical
            },
            'gpu': {
                'max_usage': 25,               # 25% maximum
                'warning_threshold': 20,       # 20% warning
                'critical_threshold': 15       # 15% critical
            },
            'disk': {
                'max_usage': 75,               # 75% maximum
                'warning_threshold': 70,       # 70% warning
                'critical_threshold': 85       # 85% critical
            },
            'temperature': {
                'max': 80,                    # 80°C maximum
                'warning_threshold': 75,      # 75°C warning
                'critical_threshold': 85      # 85°C critical
            }
        }
        
        # Intervals de surveillance
        self.monitoring_intervals = {
            'cpu': 5,                         # 5 secondes
            'memory': 10,                     # 10 secondes
            'gpu': 10,                        # 10 secondes
            'disk': 30,                       # 30 secondes
            'temperature': 30                 # 30 secondes
        }
        
        # Configuration des notifications
        self.notification_config = {
            'channels': ['email', 'slack'],
            'alert_frequency': {
                'warning': 2,                  # 2/h maximum
                'critical': 4                 # 4/h maximum
            },
            'retry_attempts': 3,
            'retry_delay': 60                 # 60 secondes entre tentatives
        }
        
        # Statistiques
        self.stats = {
            'cpu': [],
            'memory': [],
            'gpu': [],
            'disk': [],
            'temperature': []
        }
        
        self.logger.info("Système de surveillance initialisé")

    async def check_resources(self) -> bool:
        """Vérifie les ressources système et retourne True si tout est OK"""
        try:
            # Vérifier CPU
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > self.safety_limits['cpu']['max_usage']:
                self.logger.warning(f"CPU usage high: {cpu_usage}%")
                return False
            
            # Vérifier RAM
            ram = psutil.virtual_memory()
            if ram.available < self.safety_limits['memory']['min_available']:
                self.logger.warning(f"Low RAM: {ram.available / (1024**3):.1f}GB available")
                return False
            
            # Vérifier GPU
            # TODO: Implémenter la surveillance GPU
            
            # Vérifier disque
            disk = psutil.disk_usage('/')
            if disk.percent > self.safety_limits['disk']['max_usage']:
                self.logger.warning(f"Disk usage high: {disk.percent}%")
                return False
            
            # Vérifier température
            temp = self.get_temperature()
            if temp > self.safety_limits['temperature']['max']:
                self.logger.warning(f"High temperature: {temp}°C")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des ressources: {e}")
            return False

    def get_temperature(self) -> float:
        """Récupère la température du système"""
        try:
            result = subprocess.run(['smc', '-k', 'TC0P', '-r'], 
                                  capture_output=True, 
                                  text=True)
            temp = float(result.stdout.split()[2])
            return temp
        except:
            return 80  # Température par défaut si la commande échoue

    async def monitor_system(self):
        """Surveille continuellement le système"""
        while True:
            try:
                # Vérifier CPU
                cpu = psutil.cpu_percent(interval=1)
                if cpu > self.safety_limits['cpu']['warning_threshold']:
                    self.logger.warning(f"CPU usage high: {cpu}%")
                    await self.send_alert('cpu', cpu)
                
                # Vérifier RAM
                ram = psutil.virtual_memory().available / (1024 ** 3)
                if ram < self.safety_limits['memory']['warning_threshold']:
                    self.logger.warning(f"Low RAM: {ram:.1f}GB available")
                    await self.send_alert('memory', ram)
                
                # Vérifier disque
                disk = psutil.disk_usage('/')
                if disk.percent > self.safety_limits['disk']['warning_threshold']:
                    self.logger.warning(f"Disk usage high: {disk.percent}%")
                    await self.send_alert('disk', disk.percent)
                
                # Vérifier température
                temp = self.get_temperature()
                if temp > self.safety_limits['temperature']['warning_threshold']:
                    self.logger.warning(f"High temperature: {temp}°C")
                    await self.send_alert('temperature', temp)
                
                # Mettre à jour les statistiques
                self.update_stats(
                    cpu=cpu,
                    ram=ram,
                    disk=disk.percent,
                    temperature=temp
                )
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance du système: {e}")
                await asyncio.sleep(5)

    async def send_alert(self, resource: str, value: float) -> None:
        """Envoie une alerte si nécessaire"""
        if self.should_send_alert(resource):
            try:
                # TODO: Implémenter l'envoi d'alertes via les canaux configurés
                self.logger.info(f"Alert sent for {resource}: {value}")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'envoi de l'alerte: {e}")

    def should_send_alert(self, resource: str) -> bool:
        """Détermine si une alerte doit être envoyée"""
        # TODO: Implémenter la logique de fréquence des alertes
        return True

    def update_stats(self, **kwargs) -> None:
        """Mise à jour des statistiques"""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key].append(value)
                # Garder seulement les dernières 100 valeurs
                if len(self.stats[key]) > 100:
                    self.stats[key] = self.stats[key][-100:]

    async def stop(self) -> None:
        """Arrête le moniteur"""
        self.logger.info("Arrêt du moniteur...")
        # TODO: Implémenter la fermeture propre des ressources

    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques"""
        return self.stats

    def get_current_status(self) -> Dict[str, Any]:
        """Récupère l'état actuel du système"""
        return {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().available / (1024 ** 3),
            'disk': psutil.disk_usage('/').percent,
            'temperature': self.get_temperature()
        }
