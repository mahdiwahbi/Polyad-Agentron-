import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

class CompressionMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.compression')
        
        # Métriques Prometheus
        self.metrics = {
            'compression_ratio': Gauge('compression_ratio', 'Ratio de compression', ['method']),
            'compression_time': Gauge('compression_time', 'Temps de compression', ['method']),
            'decompression_time': Gauge('decompression_time', 'Temps de décompression', ['method']),
            'memory_usage': Gauge('compression_memory_usage', 'Utilisation de la mémoire'),
            'cpu_usage': Gauge('compression_cpu_usage', 'Utilisation du CPU')
        }
        
        # Statistiques
        self.stats = {
            'total_compressed': 0,
            'total_uncompressed': 0,
            'compression_times': [],
            'decompression_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'last_reset': time.time()
        }

    def monitor_compression(self, 
                          method: str, 
                          original_size: int, 
                          compressed_size: int, 
                          compression_time: float,
                          memory_usage: float,
                          cpu_usage: float) -> None:
        """Surveille une opération de compression"""
        self.stats['total_compressed'] += compressed_size
        self.stats['total_uncompressed'] += original_size
        self.stats['compression_times'].append(compression_time)
        self.stats['memory_usage'].append(memory_usage)
        self.stats['cpu_usage'].append(cpu_usage)
        
        # Mettre à jour les métriques
        self.metrics['compression_ratio'].labels(method=method).set(
            compressed_size / original_size if original_size > 0 else 0
        )
        self.metrics['compression_time'].labels(method=method).set(compression_time)
        self.metrics['memory_usage'].set(memory_usage)
        self.metrics['cpu_usage'].set(cpu_usage)

    def monitor_decompression(self, 
                            method: str, 
                            decompression_time: float,
                            memory_usage: float,
                            cpu_usage: float) -> None:
        """Surveille une opération de décompression"""
        self.stats['decompression_times'].append(decompression_time)
        self.stats['memory_usage'].append(memory_usage)
        self.stats['cpu_usage'].append(cpu_usage)
        
        # Mettre à jour les métriques
        self.metrics['decompression_time'].labels(method=method).set(decompression_time)
        self.metrics['memory_usage'].set(memory_usage)
        self.metrics['cpu_usage'].set(cpu_usage)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtient les métriques de performance"""
        if not self.stats['total_uncompressed']:
            return {
                'compression_ratio': 0,
                'average_compression_time': 0,
                'average_decompression_time': 0,
                'memory_usage': 0,
                'cpu_usage': 0
            }
            
        return {
            'compression_ratio': (
                self.stats['total_compressed'] / self.stats['total_uncompressed']
            ),
            'average_compression_time': sum(self.stats['compression_times']) / len(self.stats['compression_times']),
            'average_decompression_time': sum(self.stats['decompression_times']) / len(self.stats['decompression_times']),
            'memory_usage': sum(self.stats['memory_usage']) / len(self.stats['memory_usage']),
            'cpu_usage': sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage'])
        }

    def get_method_efficiency(self) -> Dict[str, Any]:
        """Obtient l'efficacité des méthodes de compression"""
        efficiency = {}
        
        for method in self.config.get('methods', []):
            compressed = self.stats['total_compressed']
            uncompressed = self.stats['total_uncompressed']
            
            efficiency[method] = {
                'ratio': compressed / uncompressed if uncompressed > 0 else 0,
                'compression_time': self.metrics['compression_time'].labels(method=method).get() or 0,
                'decompression_time': self.metrics['decompression_time'].labels(method=method).get() or 0,
                'memory_usage': self.metrics['memory_usage'].get() or 0,
                'cpu_usage': self.metrics['cpu_usage'].get() or 0
            }
        
        return efficiency

    def get_resource_usage(self) -> Dict[str, Any]:
        """Obtient l'utilisation des ressources"""
        return {
            'memory': {
                'current': self.metrics['memory_usage'].get() or 0,
                'average': sum(self.stats['memory_usage']) / len(self.stats['memory_usage']) if self.stats['memory_usage'] else 0,
                'peak': max(self.stats['memory_usage']) if self.stats['memory_usage'] else 0
            },
            'cpu': {
                'current': self.metrics['cpu_usage'].get() or 0,
                'average': sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage']) if self.stats['cpu_usage'] else 0,
                'peak': max(self.stats['cpu_usage']) if self.stats['cpu_usage'] else 0
            }
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé"""
        metrics = self.get_performance_metrics()
        efficiency = self.get_method_efficiency()
        resource_usage = self.get_resource_usage()
        
        # Calculer les scores
        performance_score = (
            (1 - metrics['compression_ratio']) + 
            metrics['average_compression_time'] + 
            metrics['average_decompression_time']
        )
        
        resource_score = (
            (resource_usage['memory']['current'] / self.config.get('max_memory', 100)) +
            (resource_usage['cpu']['current'] / self.config.get('max_cpu', 100))
        )
        
        status = 'healthy'
        if performance_score > 0.5:
            status = 'warning'
        if resource_score > 0.8:
            status = 'warning'
        if performance_score > 1 or resource_score > 1:
            status = 'critical'
            
        return {
            'status': status,
            'performance_metrics': metrics,
            'method_efficiency': efficiency,
            'resource_usage': resource_usage,
            'last_reset': datetime.fromtimestamp(self.stats['last_reset']).isoformat()
        }
