import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta
from prometheus_client import Gauge, Counter
from utils.logger import logger
from config.monitoring_thresholds import (
    RESOURCE_THRESHOLDS,
    PERFORMANCE_THRESHOLDS,
    ALERT_THRESHOLDS,
    TIME_WINDOWS,
    NOTIFICATION_CONFIG
)

class IntegratedMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.integrated')
        
        # Métriques Prometheus
        self.metrics = {
            # Ressources
            'cpu_usage': Gauge('polyad_cpu_usage', 'Utilisation CPU (%)'),
            'memory_usage': Gauge('polyad_memory_usage', 'Utilisation RAM (Mo)'),
            'gpu_usage': Gauge('polyad_gpu_usage', 'Utilisation GPU (%)'),
            'disk_usage': Gauge('polyad_disk_usage', 'Utilisation disque (%)'),
            
            # Performance
            'response_time': Gauge('polyad_response_time', 'Temps de réponse (ms)'),
            'throughput': Gauge('polyad_throughput', 'Débit (req/min)'),
            'error_rate': Gauge('polyad_error_rate', 'Taux d'erreur (%)'),
            'latency': Gauge('polyad_latency', 'Latence (ms)'),
            
            # Alertes
            'alert_count': Counter('polyad_alert_count_total', 'Nombre total d'alertes'),
            'alert_failure_rate': Gauge('polyad_alert_failure_rate', 'Taux d'échec des alertes (%)'),
            'inactive_channels': Gauge('polyad_inactive_channels', 'Nombre de canaux inactifs')
        }
        
        # Statistiques
        self.stats = {
            'resources': {
                'cpu': [],
                'memory': [],
                'gpu': [],
                'disk': []
            },
            'performance': {
                'response_times': [],
                'throughput': [],
                'errors': 0,
                'successes': 0
            },
            'alerts': {
                'sent': 0,
                'failed': 0,
                'last_alert': None,
                'inactive_channels': set()
            },
            'last_check': time.time()
        }

    def check_resources(self) -> Dict[str, Any]:
        """Vérifie l'état des ressources"""
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        self.stats['resources']['cpu'].append(cpu_usage)
        self.metrics['cpu_usage'].set(cpu_usage)
        
        # Mémoire
        memory = psutil.virtual_memory()
        memory_usage = memory.total / (1024 ** 2) - memory.available / (1024 ** 2)
        self.stats['resources']['memory'].append(memory_usage)
        self.metrics['memory_usage'].set(memory_usage)
        
        # GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_usage = gpus[0].load * 100
                self.stats['resources']['gpu'].append(gpu_usage)
                self.metrics['gpu_usage'].set(gpu_usage)
        except:
            gpu_usage = 0
            self.logger.warning("Impossible de détecter l'utilisation du GPU")
        
        # Disque
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        self.stats['resources']['disk'].append(disk_usage)
        self.metrics['disk_usage'].set(disk_usage)
        
        # Vérifier les seuils
        alerts = self._check_resource_thresholds(cpu_usage, memory_usage, gpu_usage, disk_usage)
        
        return {
            'cpu': cpu_usage,
            'memory': memory_usage,
            'gpu': gpu_usage,
            'disk': disk_usage,
            'alerts': alerts,
            'last_check': datetime.now().isoformat()
        }

    def check_performance(self, 
                         response_time: float, 
                         success: bool, 
                         throughput: float) -> Dict[str, Any]:
        """Vérifie les métriques de performance"""
        self.stats['performance']['response_times'].append(response_time)
        self.stats['performance']['throughput'].append(throughput)
        
        if success:
            self.stats['performance']['successes'] += 1
        else:
            self.stats['performance']['errors'] += 1
            
        # Mettre à jour les métriques
        self.metrics['response_time'].set(response_time * 1000)  # en ms
        self.metrics['throughput'].set(throughput)
        self.metrics['error_rate'].set(
            (self.stats['performance']['errors'] / 
             (self.stats['performance']['errors'] + self.stats['performance']['successes'])) * 100
        )
        
        # Calculer la latence
        if self.stats['performance']['response_times']:
            latency = sum(self.stats['performance']['response_times']) / len(self.stats['performance']['response_times'])
            self.metrics['latency'].set(latency * 1000)  # en ms
        
        # Vérifier les seuils
        alerts = self._check_performance_thresholds(response_time, throughput)
        
        return {
            'response_time': response_time,
            'throughput': throughput,
            'error_rate': self.metrics['error_rate'].get(),
            'latency': self.metrics['latency'].get() / 1000,  # en s
            'alerts': alerts,
            'last_check': datetime.now().isoformat()
        }

    def check_alert_system(self) -> Dict[str, Any]:
        """Vérifie le système d'alertes"""
        # Calculer le taux d'échec
        failure_rate = (
            self.stats['alerts']['failed'] / 
            (self.stats['alerts']['sent'] + self.stats['alerts']['failed'])
            if self.stats['alerts']['sent'] + self.stats['alerts']['failed'] > 0 else 0
        )
        self.metrics['alert_failure_rate'].set(failure_rate * 100)
        
        # Vérifier les canaux inactifs
        inactive_channels = len(self.stats['alerts']['inactive_channels'])
        self.metrics['inactive_channels'].set(inactive_channels)
        
        # Vérifier la fréquence des alertes
        alert_frequency = self.stats['alerts']['sent'] / (
            (time.time() - self.stats['last_check']) / 3600
        )  # alertes/heure
        
        # Vérifier les seuils
        alerts = self._check_alert_thresholds(failure_rate, inactive_channels, alert_frequency)
        
        return {
            'failure_rate': failure_rate * 100,
            'inactive_channels': inactive_channels,
            'alert_frequency': alert_frequency,
            'alerts': alerts,
            'last_check': datetime.now().isoformat()
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé global"""
        # Ressources
        resource_stats = {
            'cpu': sum(self.stats['resources']['cpu']) / len(self.stats['resources']['cpu']) if self.stats['resources']['cpu'] else 0,
            'memory': sum(self.stats['resources']['memory']) / len(self.stats['resources']['memory']) if self.stats['resources']['memory'] else 0,
            'gpu': sum(self.stats['resources']['gpu']) / len(self.stats['resources']['gpu']) if self.stats['resources']['gpu'] else 0,
            'disk': sum(self.stats['resources']['disk']) / len(self.stats['resources']['disk']) if self.stats['resources']['disk'] else 0
        }
        
        # Performance
        performance_stats = {
            'response_time': sum(self.stats['performance']['response_times']) / len(self.stats['performance']['response_times']) if self.stats['performance']['response_times'] else 0,
            'throughput': sum(self.stats['performance']['throughput']) / len(self.stats['performance']['throughput']) if self.stats['performance']['throughput'] else 0,
            'error_rate': (self.stats['performance']['errors'] / 
                         (self.stats['performance']['errors'] + self.stats['performance']['successes'])) * 100
                         if self.stats['performance']['errors'] + self.stats['performance']['successes'] > 0 else 0,
            'latency': sum(self.stats['performance']['response_times']) / len(self.stats['performance']['response_times']) if self.stats['performance']['response_times'] else 0
        }
        
        # Alertes
        alert_stats = {
            'failure_rate': (self.stats['alerts']['failed'] / 
                           (self.stats['alerts']['sent'] + self.stats['alerts']['failed'])) * 100
                           if self.stats['alerts']['sent'] + self.stats['alerts']['failed'] > 0 else 0,
            'inactive_channels': len(self.stats['alerts']['inactive_channels']),
            'alert_frequency': self.stats['alerts']['sent'] / (
                (time.time() - self.stats['last_check']) / 3600
            )  # alertes/heure
        }
        
        # Calculer le score de santé
        health_score = (
            (resource_stats['cpu'] / RESOURCE_THRESHOLDS['cpu']['critical']) +
            (resource_stats['memory'] / RESOURCE_THRESHOLDS['memory']['critical']) +
            (resource_stats['gpu'] / RESOURCE_THRESHOLDS['gpu']['critical']) +
            (resource_stats['disk'] / RESOURCE_THRESHOLDS['disk']['critical']) +
            (performance_stats['response_time'] / PERFORMANCE_THRESHOLDS['response_time']['critical']) +
            (alert_stats['failure_rate'] / ALERT_THRESHOLDS['failure_rate']['critical'])
        ) / 6
        
        status = 'healthy'
        if health_score > 0.7:
            status = 'warning'
        if health_score > 0.9:
            status = 'critical'
            
        return {
            'status': status,
            'health_score': health_score,
            'resource_stats': resource_stats,
            'performance_stats': performance_stats,
            'alert_stats': alert_stats,
            'last_check': datetime.fromtimestamp(self.stats['last_check']).isoformat()
        }

    def _check_resource_thresholds(self, 
                                 cpu: float, 
                                 memory: float, 
                                 gpu: float, 
                                 disk: float) -> Dict[str, str]:
        """Vérifie les seuils des ressources"""
        alerts = {
            'cpu': 'ok',
            'memory': 'ok',
            'gpu': 'ok',
            'disk': 'ok'
        }
        
        # CPU
        if cpu > RESOURCE_THRESHOLDS['cpu']['warning']:
            alerts['cpu'] = 'warning'
        if cpu > RESOURCE_THRESHOLDS['cpu']['critical']:
            alerts['cpu'] = 'critical'
        
        # Mémoire
        if memory < RESOURCE_THRESHOLDS['memory']['warning']:
            alerts['memory'] = 'warning'
        if memory < RESOURCE_THRESHOLDS['memory']['critical']:
            alerts['memory'] = 'critical'
        
        # GPU
        if gpu > RESOURCE_THRESHOLDS['gpu']['warning']:
            alerts['gpu'] = 'warning'
        if gpu > RESOURCE_THRESHOLDS['gpu']['critical']:
            alerts['gpu'] = 'critical'
        
        # Disque
        if disk > RESOURCE_THRESHOLDS['disk']['warning']:
            alerts['disk'] = 'warning'
        if disk > RESOURCE_THRESHOLDS['disk']['critical']:
            alerts['disk'] = 'critical'
        
        return alerts

    def _check_performance_thresholds(self, 
                                    response_time: float, 
                                    throughput: float) -> Dict[str, str]:
        """Vérifie les seuils de performance"""
        alerts = {
            'response_time': 'ok',
            'throughput': 'ok'
        }
        
        # Temps de réponse
        if response_time > PERFORMANCE_THRESHOLDS['response_time']['warning']:
            alerts['response_time'] = 'warning'
        if response_time > PERFORMANCE_THRESHOLDS['response_time']['critical']:
            alerts['response_time'] = 'critical'
        
        # Débit
        if throughput < PERFORMANCE_THRESHOLDS['throughput']['warning']:
            alerts['throughput'] = 'warning'
        if throughput < PERFORMANCE_THRESHOLDS['throughput']['critical']:
            alerts['throughput'] = 'critical'
        
        return alerts

    def _check_alert_thresholds(self, 
                              failure_rate: float, 
                              inactive_channels: int, 
                              alert_frequency: float) -> Dict[str, str]:
        """Vérifie les seuils du système d'alertes"""
        alerts = {
            'failure_rate': 'ok',
            'inactive_channels': 'ok',
            'alert_frequency': 'ok'
        }
        
        # Taux d'échec
        if failure_rate > ALERT_THRESHOLDS['failure_rate']['warning']:
            alerts['failure_rate'] = 'warning'
        if failure_rate > ALERT_THRESHOLDS['failure_rate']['critical']:
            alerts['failure_rate'] = 'critical'
        
        # Canaux inactifs
        if inactive_channels > ALERT_THRESHOLDS['inactive_channels']['warning']:
            alerts['inactive_channels'] = 'warning'
        if inactive_channels > ALERT_THRESHOLDS['inactive_channels']['critical']:
            alerts['inactive_channels'] = 'critical'
        
        # Fréquence des alertes
        if alert_frequency > ALERT_THRESHOLDS['alert_frequency']['warning']:
            alerts['alert_frequency'] = 'warning'
        if alert_frequency > ALERT_THRESHOLDS['alert_frequency']['critical']:
            alerts['alert_frequency'] = 'critical'
        
        return alerts

    def reset_statistics(self) -> None:
        """Réinitialise les statistiques"""
        self.stats = {
            'resources': {
                'cpu': [],
                'memory': [],
                'gpu': [],
                'disk': []
            },
            'performance': {
                'response_times': [],
                'throughput': [],
                'errors': 0,
                'successes': 0
            },
            'alerts': {
                'sent': 0,
                'failed': 0,
                'last_alert': None,
                'inactive_channels': set()
            },
            'last_check': time.time()
        }
        
        # Réinitialiser les métriques
        for metric in self.metrics.values():
            metric.clear()
