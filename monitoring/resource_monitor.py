import psutil
import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

class ResourceMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.resource')
        
        # Configuration des seuils
        self.thresholds = {
            'cpu': {
                'warning': 80,
                'critical': 90
            },
            'memory': {
                'warning': 1,
                'critical': 0.5
            },
            'gpu': {
                'warning': 90,
                'critical': 95
            },
            'disk': {
                'warning': 85,
                'critical': 95
            }
        }
        
        # Métriques Prometheus
        self.metrics = {
            'cpu_usage': Gauge('polyad_cpu_usage', 'Utilisation CPU (%)'),
            'memory_usage': Gauge('polyad_memory_usage', 'Utilisation RAM (Go)'),
            'gpu_usage': Gauge('polyad_gpu_usage', 'Utilisation GPU (%)'),
            'disk_usage': Gauge('polyad_disk_usage', 'Utilisation disque (%)'),
            'resource_warnings': Counter('polyad_resource_warnings_total', 'Avertissements ressources'),
            'resource_criticals': Counter('polyad_resource_criticals_total', 'Alertes critiques ressources')
        }
        
        # Statistiques
        self.stats = {
            'cpu': [],
            'memory': [],
            'gpu': [],
            'disk': [],
            'last_check': time.time()
        }

    def check_resources(self) -> Dict[str, Any]:
        """Vérifie l'état des ressources"""
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        self.stats['cpu'].append(cpu_usage)
        self.metrics['cpu_usage'].set(cpu_usage)
        
        # Mémoire
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        self.stats['memory'].append(memory_usage)
        self.metrics['memory_usage'].set(memory.total / (1024 ** 3) - memory.available / (1024 ** 3))
        
        # GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_usage = gpus[0].load * 100
                self.stats['gpu'].append(gpu_usage)
                self.metrics['gpu_usage'].set(gpu_usage)
        except:
            gpu_usage = 0
            self.logger.warning("Impossible de détecter l'utilisation du GPU")
        
        # Disque
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        self.stats['disk'].append(disk_usage)
        self.metrics['disk_usage'].set(disk_usage)
        
        # Vérifier les seuils
        alerts = self._check_thresholds(cpu_usage, memory_usage, gpu_usage, disk_usage)
        
        return {
            'cpu': cpu_usage,
            'memory': memory_usage,
            'gpu': gpu_usage,
            'disk': disk_usage,
            'alerts': alerts,
            'last_check': datetime.now().isoformat()
        }

    def _check_thresholds(self, cpu: float, memory: float, gpu: float, disk: float) -> Dict[str, Any]:
        """Vérifie les seuils et génère des alertes"""
        alerts = {
            'cpu': 'ok',
            'memory': 'ok',
            'gpu': 'ok',
            'disk': 'ok'
        }
        
        # CPU
        if cpu > self.thresholds['cpu']['warning']:
            alerts['cpu'] = 'warning'
            self.metrics['resource_warnings'].inc()
        if cpu > self.thresholds['cpu']['critical']:
            alerts['cpu'] = 'critical'
            self.metrics['resource_criticals'].inc()
        
        # Mémoire
        if memory > self.thresholds['memory']['warning']:
            alerts['memory'] = 'warning'
            self.metrics['resource_warnings'].inc()
        if memory > self.thresholds['memory']['critical']:
            alerts['memory'] = 'critical'
            self.metrics['resource_criticals'].inc()
        
        # GPU
        if gpu > self.thresholds['gpu']['warning']:
            alerts['gpu'] = 'warning'
            self.metrics['resource_warnings'].inc()
        if gpu > self.thresholds['gpu']['critical']:
            alerts['gpu'] = 'critical'
            self.metrics['resource_criticals'].inc()
        
        # Disque
        if disk > self.thresholds['disk']['warning']:
            alerts['disk'] = 'warning'
            self.metrics['resource_warnings'].inc()
        if disk > self.thresholds['disk']['critical']:
            alerts['disk'] = 'critical'
            self.metrics['resource_criticals'].inc()
        
        return alerts

    def get_resource_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des ressources"""
        return {
            'cpu': {
                'average': sum(self.stats['cpu']) / len(self.stats['cpu']) if self.stats['cpu'] else 0,
                'peak': max(self.stats['cpu']) if self.stats['cpu'] else 0
            },
            'memory': {
                'average': sum(self.stats['memory']) / len(self.stats['memory']) if self.stats['memory'] else 0,
                'peak': max(self.stats['memory']) if self.stats['memory'] else 0
            },
            'gpu': {
                'average': sum(self.stats['gpu']) / len(self.stats['gpu']) if self.stats['gpu'] else 0,
                'peak': max(self.stats['gpu']) if self.stats['gpu'] else 0
            },
            'disk': {
                'average': sum(self.stats['disk']) / len(self.stats['disk']) if self.stats['disk'] else 0,
                'peak': max(self.stats['disk']) if self.stats['disk'] else 0
            },
            'last_check': datetime.fromtimestamp(self.stats['last_check']).isoformat()
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé"""
        stats = self.get_resource_statistics()
        
        # Calculer le score de santé
        health_score = (
            (stats['cpu']['peak'] / 100) +
            (stats['memory']['peak'] / 100) +
            (stats['gpu']['peak'] / 100) +
            (stats['disk']['peak'] / 100)
        ) / 4
        
        status = 'healthy'
        if health_score > 0.7:
            status = 'warning'
        if health_score > 0.9:
            status = 'critical'
            
        return {
            'status': status,
            'health_score': health_score,
            'resource_stats': stats,
            'alerts': self._check_thresholds(
                stats['cpu']['peak'],
                stats['memory']['peak'],
                stats['gpu']['peak'],
                stats['disk']['peak']
            )
        }
