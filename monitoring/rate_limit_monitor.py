import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

class RateLimitMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.rate_limit')
        
        # Métriques Prometheus
        self.metrics = {
            'requests': Counter('rate_limit_requests_total', 'Nombre total de requêtes', ['type', 'identifier']),
            'blocked': Counter('rate_limit_blocked_total', 'Nombre de requêtes bloquées', ['type', 'identifier']),
            'bursts': Counter('rate_limit_bursts_total', 'Nombre de bursts utilisés', ['identifier']),
            'whitelist': Gauge('rate_limit_whitelist_size', 'Taille de la whitelist'),
            'current_rate': Gauge('rate_limit_current_rate', 'Taux actuel de requêtes', ['type', 'identifier']),
            'response_time': Gauge('rate_limit_response_time', 'Temps de réponse', ['type', 'identifier'])
        }
        
        # Statistiques
        self.stats = {
            'requests': 0,
            'blocked': 0,
            'bursts': 0,
            'response_times': [],
            'last_reset': time.time()
        }

    def monitor_request(self, 
                       identifier: str, 
                       limit_type: str, 
                       is_blocked: bool, 
                       response_time: float,
                       used_burst: bool = False) -> None:
        """Surveille une requête"""
        self.stats['requests'] += 1
        self.metrics['requests'].labels(type=limit_type, identifier=identifier).inc()
        
        if is_blocked:
            self.stats['blocked'] += 1
            self.metrics['blocked'].labels(type=limit_type, identifier=identifier).inc()
        
        if used_burst:
            self.stats['bursts'] += 1
            self.metrics['bursts'].labels(identifier=identifier).inc()
        
        self.stats['response_times'].append(response_time)
        self.metrics['response_time'].labels(type=limit_type, identifier=identifier).set(response_time)
        
        # Mettre à jour le taux actuel
        current_time = time.time()
        if current_time - self.stats['last_reset'] > 60:
            self._reset_stats()
        
        self.metrics['current_rate'].labels(type=limit_type, identifier=identifier).set(
            self.stats['requests'] / (current_time - self.stats['last_reset'])
        )

    def _reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self.stats['requests'] = 0
        self.stats['blocked'] = 0
        self.stats['bursts'] = 0
        self.stats['response_times'] = []
        self.stats['last_reset'] = time.time()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtient les métriques de performance"""
        if not self.stats['requests']:
            return {
                'requests_per_second': 0,
                'block_rate': 0,
                'burst_rate': 0,
                'average_response_time': 0,
                '95th_percentile_response_time': 0
            }
            
        current_time = time.time()
        time_elapsed = current_time - self.stats['last_reset']
        
        return {
            'requests_per_second': self.stats['requests'] / time_elapsed,
            'block_rate': (self.stats['blocked'] / self.stats['requests']) * 100,
            'burst_rate': (self.stats['bursts'] / self.stats['requests']) * 100,
            'average_response_time': sum(self.stats['response_times']) / len(self.stats['response_times']),
            '95th_percentile_response_time': self._calculate_percentile(95)
        }

    def _calculate_percentile(self, percentile: float) -> float:
        """Calcule le percentile des temps de réponse"""
        if not self.stats['response_times']:
            return 0
            
        sorted_times = sorted(self.stats['response_times'])
        index = int(len(sorted_times) * (percentile / 100))
        return sorted_times[index]

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé"""
        metrics = self.get_performance_metrics()
        
        return {
            'status': 'healthy' if metrics['block_rate'] < 10 else 'warning',
            'metrics': metrics,
            'last_reset': datetime.fromtimestamp(self.stats['last_reset']).isoformat()
        }
