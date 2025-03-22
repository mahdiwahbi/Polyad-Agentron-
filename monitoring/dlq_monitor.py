import logging
from typing import Dict, Any, Optional, List
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

class DLQMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.dlq')
        
        # Métriques Prometheus
        self.metrics = {
            'messages': Gauge('dlq_messages_total', 'Nombre total de messages'),
            'pending': Gauge('dlq_pending_total', 'Messages en attente'),
            'processing': Gauge('dlq_processing_total', 'Messages en traitement'),
            'failed': Gauge('dlq_failed_total', 'Messages échoués'),
            'retries': Counter('dlq_retries_total', 'Nombre de retries'),
            'delivery_time': Gauge('dlq_delivery_time', 'Temps de livraison'),
            'queue_size': Gauge('dlq_queue_size', 'Taille de la file d'attente')
        }
        
        # Statistiques
        self.stats = {
            'messages': 0,
            'pending': 0,
            'processing': 0,
            'failed': 0,
            'retries': 0,
            'delivery_times': [],
            'queue_sizes': [],
            'last_reset': time.time()
        }

    def monitor_message(self, 
                      status: str, 
                      delivery_time: float,
                      queue_size: int) -> None:
        """Surveille un message"""
        self.stats['messages'] += 1
        self.stats['delivery_times'].append(delivery_time)
        self.stats['queue_sizes'].append(queue_size)
        
        # Mettre à jour les métriques
        self.metrics['messages'].set(self.stats['messages'])
        self.metrics['delivery_time'].set(delivery_time)
        self.metrics['queue_size'].set(queue_size)
        
        # Mettre à jour le statut
        if status == 'pending':
            self.stats['pending'] += 1
            self.metrics['pending'].inc()
        elif status == 'processing':
            self.stats['processing'] += 1
            self.metrics['processing'].inc()
        elif status == 'failed':
            self.stats['failed'] += 1
            self.metrics['failed'].inc()

    def monitor_retry(self, message_id: str, retry_count: int) -> None:
        """Surveille un retry"""
        self.stats['retries'] += 1
        self.metrics['retries'].inc()
        
        # Mettre à jour les métriques
        self.metrics['retries'].labels(message_id=message_id).inc()

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de la file d'attente"""
        return {
            'messages': self.stats['messages'],
            'pending': self.stats['pending'],
            'processing': self.stats['processing'],
            'failed': self.stats['failed'],
            'retries': self.stats['retries'],
            'average_delivery_time': sum(self.stats['delivery_times']) / len(self.stats['delivery_times']) if self.stats['delivery_times'] else 0,
            '95th_percentile_delivery_time': self._calculate_percentile(self.stats['delivery_times'], 95),
            'average_queue_size': sum(self.stats['queue_sizes']) / len(self.stats['queue_sizes']) if self.stats['queue_sizes'] else 0,
            '95th_percentile_queue_size': self._calculate_percentile(self.stats['queue_sizes'], 95)
        }

    def get_retry_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des retries"""
        return {
            'total_retries': self.stats['retries'],
            'retry_rate': (self.stats['retries'] / self.stats['messages']) * 100 if self.stats['messages'] > 0 else 0,
            'successful_retries': len([m for m in self.stats['messages'] if m['status'] == 'processed' and m['retries'] > 0]),
            'failed_retries': len([m for m in self.stats['messages'] if m['status'] == 'abandoned'])
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé"""
        queue_stats = self.get_queue_statistics()
        retry_stats = self.get_retry_statistics()
        
        # Calculer les scores
        queue_score = (
            queue_stats['pending'] / queue_stats['messages'] if queue_stats['messages'] > 0 else 0 +
            queue_stats['failed'] / queue_stats['messages'] if queue_stats['messages'] > 0 else 0
        )
        
        retry_score = (
            retry_stats['retry_rate'] +
            retry_stats['failed_retries'] / retry_stats['total_retries'] if retry_stats['total_retries'] > 0 else 0
        )
        
        status = 'healthy'
        if queue_score > 0.1 or retry_score > 0.1:
            status = 'warning'
        if queue_score > 0.3 or retry_score > 0.3:
            status = 'critical'
            
        return {
            'status': status,
            'queue_statistics': queue_stats,
            'retry_statistics': retry_stats,
            'last_reset': datetime.fromtimestamp(self.stats['last_reset']).isoformat()
        }

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calcule le percentile des valeurs"""
        if not values:
            return 0
            
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[index]

    def reset_statistics(self) -> None:
        """Réinitialise les statistiques"""
        self.stats = {
            'messages': 0,
            'pending': 0,
            'processing': 0,
            'failed': 0,
            'retries': 0,
            'delivery_times': [],
            'queue_sizes': [],
            'last_reset': time.time()
        }
        
        # Réinitialiser les métriques
        for metric in self.metrics.values():
            metric.clear()
