from prometheus_client import Counter, Histogram, Gauge, start_http_server
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
from utils.logger import logger

# Métriques Prometheus
class Metrics:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.metrics')
        
        # Configuration des métriques
        self.metrics_config = config.get('metrics', {
            'port': 8000,
            'prefix': 'polyad_'
        })
        
        # Configuration des alertes
        self.alerts_config = config.get('alerts', {
            'cpu_threshold': 80,
            'memory_threshold': 80,
            'disk_threshold': 80,
            'network_threshold': 80
        })
        
        # Initialiser les métriques Prometheus
        self._init_metrics()
        
        # Historique des alertes
        self.alert_history = []
        
        # État des alertes actives
        self.active_alerts = set()

    def _init_metrics(self):
        """Initialise les métriques Prometheus"""
        prefix = self.metrics_config['prefix']
        
        # Métriques système
        self.cpu_usage = Gauge(f'{prefix}cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge(f'{prefix}memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge(f'{prefix}disk_usage_percent', 'Disk usage percentage')
        self.network_usage = Gauge(f'{prefix}network_usage_mbps', 'Network usage in Mbps')
        self.temperature = Gauge(f'{prefix}temperature_celsius', 'System temperature in Celsius')
        
        # Métriques de performance
        self.request_latency = Histogram(f'{prefix}request_latency_seconds', 'Request latency in seconds')
        self.request_count = Counter(f'{prefix}request_count', 'Number of requests')
        self.error_count = Counter(f'{prefix}error_count', 'Number of errors', ['type'])
        
        # Métriques de ressources
        self.cache_hits = Counter(f'{prefix}cache_hits', 'Number of cache hits')
        self.cache_misses = Counter(f'{prefix}cache_misses', 'Number of cache misses')
        self.cache_size = Gauge(f'{prefix}cache_size_bytes', 'Cache size in bytes')
        
        # Métriques de sécurité
        self.login_attempts = Counter(f'{prefix}login_attempts', 'Number of login attempts', ['success'])
        self.failed_auth = Counter(f'{prefix}failed_auth', 'Number of failed authentication attempts')
        
        # Métriques de backup
        self.backup_count = Counter(f'{prefix}backup_count', 'Number of backups')
        self.backup_size = Gauge(f'{prefix}backup_size_bytes', 'Backup size in bytes')
        self.backup_duration = Histogram(f'{prefix}backup_duration_seconds', 'Backup duration in seconds')

    async def start_server(self):
        """Démarre le serveur Prometheus"""
        try:
            start_http_server(self.metrics_config['port'])
            self.logger.info(f"Serveur Prometheus démarré sur le port {self.metrics_config['port']}")
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur Prometheus: {e}")

    def record_request(self, duration: float, success: bool = True):
        """Enregistre une requête"""
        self.request_count.inc()
        self.request_latency.observe(duration)
        if not success:
            self.error_count.labels(type='request').inc()

    def record_cache_operation(self, hit: bool, size: int):
        """Enregistre une opération de cache"""
        if hit:
            self.cache_hits.inc()
        else:
            self.cache_misses.inc()
        self.cache_size.set(size)

    def record_backup(self, size: int, duration: float):
        """Enregistre un backup"""
        self.backup_count.inc()
        self.backup_size.set(size)
        self.backup_duration.observe(duration)

    def update_system_metrics(self, metrics: Dict[str, Any]):
        """Met à jour les métriques système"""
        self.cpu_usage.set(metrics.get('cpu', {}).get('percent', 0))
        self.memory_usage.set(metrics.get('memory', {}).get('ram', {}).get('percent', 0))
        self.disk_usage.set(metrics.get('disk', {}).get('percent', 0))
        network_usage = (metrics.get('network', {}).get('bytes_sent', 0) + 
                       metrics.get('network', {}).get('bytes_recv', 0)) / 1_000_000  # en Mbps
        self.network_usage.set(network_usage)
        
        # Vérifier les seuils et déclencher les alertes
        self._check_thresholds(metrics)

    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Vérifie les seuils et déclenche les alertes"""
        alerts = []
        
        # Vérifier CPU
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > self.alerts_config['cpu_threshold']:
            alerts.append({
                'type': 'cpu',
                'value': cpu_percent,
                'threshold': self.alerts_config['cpu_threshold']
            })
        
        # Vérifier mémoire
        memory_percent = metrics.get('memory', {}).get('ram', {}).get('percent', 0)
        if memory_percent > self.alerts_config['memory_threshold']:
            alerts.append({
                'type': 'memory',
                'value': memory_percent,
                'threshold': self.alerts_config['memory_threshold']
            })
        
        # Vérifier disque
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.alerts_config['disk_threshold']:
            alerts.append({
                'type': 'disk',
                'value': disk_percent,
                'threshold': self.alerts_config['disk_threshold']
            })
        
        # Vérifier réseau
        network_usage = (metrics.get('network', {}).get('bytes_sent', 0) + 
                       metrics.get('network', {}).get('bytes_recv', 0)) / 1_000_000  # en Mbps
        if network_usage > self.alerts_config['network_threshold']:
            alerts.append({
                'type': 'network',
                'value': network_usage,
                'threshold': self.alerts_config['network_threshold']
            })
        
        # Gérer les alertes
        for alert in alerts:
            alert_id = f"{alert['type']}_{datetime.now().isoformat()}"
            if alert_id not in self.active_alerts:
                self.active_alerts.add(alert_id)
                self.alert_history.append({
                    'id': alert_id,
                    'type': alert['type'],
                    'value': alert['value'],
                    'threshold': alert['threshold'],
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.warning(f"Alerte {alert['type']}: {alert['value']} dépasse {alert['threshold']}")

    def get_alert_history(self) -> list:
        """Obtient l'historique des alertes"""
        return self.alert_history.copy()

    def get_active_alerts(self) -> set:
        """Obtient les alertes actives"""
        return self.active_alerts.copy()

    def clear_alert(self, alert_id: str) -> bool:
        """Supprime une alerte"""
        if alert_id in self.active_alerts:
            self.active_alerts.remove(alert_id)
            return True
        return False

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Obtient un instantané des métriques"""
        return {
            'cpu': self.cpu_usage._value.get(),
            'memory': self.memory_usage._value.get(),
            'disk': self.disk_usage._value.get(),
            'network': self.network_usage._value.get(),
            'temperature': self.temperature._value.get(),
            'cache': {
                'hits': self.cache_hits._value.get(),
                'misses': self.cache_misses._value.get(),
                'size': self.cache_size._value.get()
            },
            'requests': {
                'count': self.request_count._value.get(),
                'errors': self.error_count._value.get()
            },
            'backups': {
                'count': self.backup_count._value.get(),
                'size': self.backup_size._value.get()
            }
        }
