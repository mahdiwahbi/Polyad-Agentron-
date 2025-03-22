import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

# Configuration des seuils par défaut pour les métriques de performance
DEFAULT_THRESHOLDS = {
    'response_time': {
        'warning': 2.0,  # en secondes
        'critical': 5.0
    },
    'throughput': {
        'warning': 100,  # requêtes par minute
        'critical': 50
    },
    'error_rate': {
        'warning': 1.0,  # en pourcentage
        'critical': 5.0
    },
    'latency': {
        'warning': 100.0,  # en millisecondes
        'critical': 500.0
    }
}

# Définition des métriques Prometheus
METRIC_DEFINITIONS = {
    'response_time': ('polyad_response_time', 'Temps de réponse (ms)'),
    'throughput': ('polyad_throughput', 'Débit (req/min)'),
    'error_rate': ('polyad_error_rate', 'Taux d\'erreur (%)'),
    'latency': ('polyad_latency', 'Latence (ms)'),
    'success_rate': ('polyad_success_rate', 'Taux de succès (%)')
}

class PerformanceMonitor:
    """
    Classe pour surveiller les performances de l'application Polyad.
    Gère les métriques de performance, les seuils d'alerte et les statistiques.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialise le moniteur de performance.
        
        Args:
            config: Configuration optionnelle pour surcharger les seuils par défaut
        """
        self.logger = logging.getLogger('polyad.monitor.performance')
        self.logger.setLevel(logging.INFO)
        
        # Configuration des seuils avec validation
        self.thresholds = DEFAULT_THRESHOLDS.copy()
        if config and 'thresholds' in config:
            self._update_thresholds(config['thresholds'])
        
        # Initialisation des métriques Prometheus
        self.metrics = self._initialize_metrics()
        
        # Initialisation des statistiques
        self.stats = {
            'response_times': [],
            'throughput': [],
            'errors': 0,
            'successes': 0,
            'last_check': time.time()
        }

    def _initialize_metrics(self) -> Dict[str, Gauge]:
        """
        Initialise les métriques Prometheus.
        
        Returns:
            Dictionnaire des métriques initialisées
        """
        metrics = {}
        for name, (metric_name, description) in METRIC_DEFINITIONS.items():
            metrics[name] = Gauge(metric_name, description)
        return metrics

    def _update_thresholds(self, new_thresholds: Dict[str, Any]) -> None:
        """
        Met à jour les seuils de performance avec validation.
        
        Args:
            new_thresholds: Nouveaux seuils à appliquer
        
        Raises:
            ValueError: Si les seuils ne sont pas valides
        """
        for metric, thresholds in new_thresholds.items():
            if metric not in self.thresholds:
                continue
            
            if not isinstance(thresholds, dict):
                raise ValueError(f"Les seuils pour {metric} doivent être un dictionnaire")
            
            if not all(key in thresholds for key in ['warning', 'critical']):
                raise ValueError(f"Les seuils pour {metric} doivent contenir 'warning' et 'critical'")
            
            if not all(isinstance(val, (int, float)) for val in thresholds.values()):
                raise ValueError(f"Les valeurs des seuils pour {metric} doivent être numériques")
            
            if thresholds['warning'] >= thresholds['critical']:
                raise ValueError(f"Le seuil warning doit être inférieur au seuil critical pour {metric}")
            
            self.thresholds[metric] = thresholds

    def monitor_request(self, 
                       response_time: float, 
                       success: bool, 
                       throughput: float) -> None:
        """
        Surveille une requête et met à jour les statistiques.
        
        Args:
            response_time: Temps de réponse en secondes
            success: Indique si la requête a réussi
            throughput: Débit en requêtes par minute
        
        Raises:
            ValueError: Si les valeurs d'entrée ne sont pas valides
        """
        if response_time < 0 or throughput < 0:
            raise ValueError("Les temps de réponse et le débit doivent être positifs")
            
        self.stats['response_times'].append(response_time)
        self.stats['throughput'].append(throughput)
        
        if success:
            self.stats['successes'] += 1
        else:
            self.stats['errors'] += 1
            
        # Mettre à jour les métriques
        self._update_metrics()

    def _update_metrics(self) -> None:
        """Met à jour toutes les métriques Prometheus."""
        try:
            avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            avg_throughput = sum(self.stats['throughput']) / len(self.stats['throughput'])
            
            total_requests = self.stats['errors'] + self.stats['successes']
            error_rate = (self.stats['errors'] / total_requests) * 100 if total_requests > 0 else 0
            success_rate = (self.stats['successes'] / total_requests) * 100 if total_requests > 0 else 0
            
            # Mettre à jour toutes les métriques
            self.metrics['response_time'].set(avg_response_time * 1000)  # en ms
            self.metrics['throughput'].set(avg_throughput)
            self.metrics['error_rate'].set(error_rate)
            self.metrics['success_rate'].set(success_rate)
            
            # Calculer et mettre à jour la latence
            latency = avg_response_time * 1000  # en ms
            self.metrics['latency'].set(latency)
            
        except ZeroDivisionError:
            self.logger.warning("Pas de données pour calculer les métriques")
            self._reset_metrics()

    def _reset_metrics(self) -> None:
        """Réinitialise toutes les métriques Prometheus."""
        for metric in self.metrics.values():
            metric.clear()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Obtient les métriques de performance actuelles.
        
        Returns:
            Dictionnaire contenant les métriques de performance
        """
        if not self.stats['response_times']:
            return self._get_default_metrics()
            
        avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
        avg_throughput = sum(self.stats['throughput']) / len(self.stats['throughput'])
        total_requests = self.stats['errors'] + self.stats['successes']
        error_rate = (self.stats['errors'] / total_requests) * 100 if total_requests > 0 else 0
        success_rate = (self.stats['successes'] / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            'response_time': avg_response_time,
            'throughput': avg_throughput,
            'error_rate': error_rate,
            'latency': avg_response_time * 1000,  # en ms
            'success_rate': success_rate
        }

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques par défaut (toutes à 0)."""
        return {
            'response_time': 0,
            'throughput': 0,
            'error_rate': 0,
            'latency': 0,
            'success_rate': 0
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtient le statut de santé de l'application basé sur les métriques.
        
        Returns:
            Dictionnaire contenant le statut de santé et les détails
        """
        metrics = self.get_performance_metrics()
        scores = self._calculate_health_scores(metrics)
        
        status = self._determine_health_status(scores)
        
        return {
            'status': status,
            'scores': scores,
            'performance_metrics': metrics,
            'last_check': datetime.fromtimestamp(self.stats['last_check']).isoformat()
        }

    def _calculate_health_scores(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les scores de santé pour chaque métrique.
        
        Args:
            metrics: Dictionnaire des métriques actuelles
            
        Returns:
            Dictionnaire des scores de santé (0.0 à 1.0)
        """
        scores = {}
        
        # Score de temps de réponse
        response_score = min(1.0, metrics['response_time'] / self.thresholds['response_time']['critical'])
        scores['response'] = response_score
        
        # Score de débit
        throughput_score = min(1.0, self.thresholds['throughput']['critical'] / metrics['throughput']) if metrics['throughput'] > 0 else 1
        scores['throughput'] = throughput_score
        
        # Score d'erreur
        error_score = min(1.0, metrics['error_rate'] / self.thresholds['error_rate']['critical'])
        scores['error'] = error_score
        
        return scores

    def _determine_health_status(self, scores: Dict[str, float]) -> str:
        """
        Détermine le statut de santé basé sur les scores.
        
        Args:
            scores: Dictionnaire des scores de santé
            
        Returns:
            Statut de santé ('healthy', 'warning' ou 'critical')
        """
        status = 'healthy'
        if any(score > 0.7 for score in scores.values()):
            status = 'warning'
        if any(score > 0.9 for score in scores.values()):
            status = 'critical'
        return status

    def reset_statistics(self) -> None:
        """Réinitialise toutes les statistiques et métriques."""
        self.stats = {
            'response_times': [],
            'throughput': [],
            'errors': 0,
            'successes': 0,
            'last_check': time.time()
        }
        self._reset_metrics()
