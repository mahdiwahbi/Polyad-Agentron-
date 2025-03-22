import logging
from typing import Dict, Any
import time
from datetime import datetime
from utils.logger import logger
from utils.notification_manager import NotificationManager
from monitoring.system_monitor import SystemMonitor

class AlertSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.alert')
        self.notification_manager = NotificationManager(config)
        self.system_monitor = SystemMonitor()
        
        # Vérification initiale de la compatibilité système
        if not self.system_monitor.check_system_compatibility():
            raise SystemExit("Configuration système incompatible")
            
        # Configuration des alertes
        self.alert_config = {
            'resource': {
                'cpu': {
                    'warning': 25,
                    'critical': 20,
                    'channels': ['email', 'slack']
                },
                'memory': {
                    'warning': 4096,
                    'critical': 3072,
                    'channels': ['email', 'slack']
                },
                'gpu': {
                    'warning': 25,
                    'critical': 20,
                    'channels': ['email', 'slack']
                },
                'disk': {
                    'warning': 75,
                    'critical': 85,
                    'channels': ['email', 'slack']
                }
            },
            'performance': {
                'response_time': {
                    'warning': 500,
                    'critical': 1000,
                    'channels': ['email', 'slack']
                },
                'throughput': {
                    'warning': 25,
                    'critical': 20,
                    'channels': ['email', 'slack']
                },
                'error_rate': {
                    'warning': 0.5,
                    'critical': 1,
                    'channels': ['email', 'slack']
                },
                'latency': {
                    'warning': 25,
                    'critical': 50,
                    'channels': ['email', 'slack']
                }
            }
        }
        
        # Statistiques des alertes
        self.alert_stats = {
            'sent': 0,
            'cpu': {'warnings': 0, 'criticals': 0},
            'memory': {'warnings': 0, 'criticals': 0},
            'gpu': {'warnings': 0, 'criticals': 0},
            'disk': {'warnings': 0, 'criticals': 0},
            'performance': {'warnings': 0, 'criticals': 0},
            'last_alert': None,
            'alerts_by_type': {
                'resource': 0,
                'performance': 0
            }
        }

    def process_alert(self, 
                     alert_type: str, 
                     alert_level: str, 
                     details: Dict[str, Any]) -> None:
        """Traite une alerte"""
        if alert_type not in self.alert_config:
            self.logger.warning(f"Type d'alerte inconnu: {alert_type}")
            return
            
        if alert_level not in ['warning', 'critical']:
            self.logger.warning(f"Niveau d'alerte invalide: {alert_level}")
            return
            
        # Préparer le message
        message = {
            'type': alert_type,
            'level': alert_level,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'channels': self.alert_config[alert_type][alert_level]['channels']
        }
        
        # Envoyer l'alerte
        try:
            self.notification_manager.send_notification(
                message['channels'],
                self.alert_config[alert_type][alert_level][alert_level],
                details
            )
            self.alert_stats['sent'] += 1
            self.alert_stats['alerts_by_type'][alert_type] += 1
            self.alert_stats['last_alert'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'alerte: {str(e)}")
            self.alert_stats['failed'] += 1

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des alertes"""
        return {
            'total_sent': self.alert_stats['sent'],
            'total_failed': self.alert_stats.get('failed', 0),
            'by_type': self.alert_stats['alerts_by_type'],
            'last_alert': self.alert_stats['last_alert'],
            'alert_rate': (
                self.alert_stats['sent'] / (self.alert_stats['sent'] + self.alert_stats.get('failed', 0))
                if self.alert_stats['sent'] + self.alert_stats.get('failed', 0) > 0 else 0
            )
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé du système d'alerte"""
        stats = self.get_alert_statistics()
        
        # Calculer le score de santé
        alert_score = (
            (stats['total_failed'] / (stats['total_sent'] + stats['total_failed']) if stats['total_sent'] + stats['total_failed'] > 0 else 0) +
            (1 - stats['alert_rate'])
        ) / 2
        
        status = 'healthy'
        if alert_score > 0.3:
            status = 'warning'
        if alert_score > 0.6:
            status = 'critical'
            
        return {
            'status': status,
            'alert_score': alert_score,
            'alert_stats': stats,
            'last_check': datetime.now().isoformat()
        }

    def check_system_safety(self) -> bool:
        """Vérifie la sécurité du système"""
        return self.system_monitor.check_system_safety()

    def monitor_system(self) -> None:
        """Surveille le système en continu"""
        self.system_monitor.monitor_system()
