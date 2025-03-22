import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Gauge, Counter
from utils.logger import logger

class NotificationSecurityMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitor.notification_security')
        
        # Métriques Prometheus
        self.metrics = {
            'sent': Counter('notification_sent_total', 'Nombre de notifications envoyées', ['provider', 'priority']),
            'failed': Counter('notification_failed_total', 'Nombre de notifications échouées', ['provider', 'priority']),
            'retry': Counter('notification_retry_total', 'Nombre de retries', ['provider', 'priority']),
            'delivery_time': Gauge('notification_delivery_time', 'Temps de livraison', ['provider', 'priority']),
            'security_incidents': Counter('notification_security_incidents_total', 'Incidents de sécurité', ['type'])
        }
        
        # Statistiques de sécurité
        self.security_stats = {
            'suspicious_patterns': 0,
            'malicious_content': 0,
            'unauthorized_access': 0,
            'last_incident': None
        }

    def monitor_notification(self, 
                           provider: str, 
                           priority: str, 
                           success: bool, 
                           delivery_time: float,
                           retry_count: int = 0) -> None:
        """Surveille une notification"""
        self.metrics['sent'].labels(provider=provider, priority=priority).inc()
        
        if not success:
            self.metrics['failed'].labels(provider=provider, priority=priority).inc()
            
        if retry_count > 0:
            self.metrics['retry'].labels(provider=provider, priority=priority).inc()
            
        self.metrics['delivery_time'].labels(provider=provider, priority=priority).set(delivery_time)

    def check_security(self, notification: Dict[str, Any]) -> bool:
        """Vérifie la sécurité d'une notification"""
        # Vérifier les patterns suspects
        suspicious_patterns = [
            r"\b(password|secret|token)\b",
            r"\b(http[s]?://[\w.]+/[\w-]+)\b",
            r"\b(\d{3}-\d{2}-\d{4})\b",
            r"\b(\d{4}-\d{2}-\d{2})\b"
        ]
        
        content = json.dumps(notification)
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.security_stats['suspicious_patterns'] += 1
                self.metrics['security_incidents'].labels(type='suspicious_pattern').inc()
                self.security_stats['last_incident'] = datetime.now().isoformat()
                return False
                
        # Vérifier le contenu malveillant
        malicious_patterns = [
            r"\b(script|iframe|eval)\b",
            r"\b(on\w+=[\s\S]+)\b",
            r"\b(data:[\s\S]+)\b",
            r"\b(base64:[\s\S]+)\b"
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.security_stats['malicious_content'] += 1
                self.metrics['security_incidents'].labels(type='malicious_content').inc()
                self.security_stats['last_incident'] = datetime.now().isoformat()
                return False
                
        # Vérifier l'accès non autorisé
        if notification.get('user_id') not in self.config.get('authorized_users', []):
            self.security_stats['unauthorized_access'] += 1
            self.metrics['security_incidents'].labels(type='unauthorized_access').inc()
            self.security_stats['last_incident'] = datetime.now().isoformat()
            return False
            
        return True

    def get_security_metrics(self) -> Dict[str, Any]:
        """Obtient les métriques de sécurité"""
        return {
            'suspicious_patterns': self.security_stats['suspicious_patterns'],
            'malicious_content': self.security_stats['malicious_content'],
            'unauthorized_access': self.security_stats['unauthorized_access'],
            'last_incident': self.security_stats['last_incident']
        }

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de livraison"""
        delivery_times = []
        for provider in self.config.get('providers', []):
            for priority in self.config.get('priorities', []):
                delivery_times.extend(
                    self.metrics['delivery_time'].labels(provider=provider, priority=priority).get() or []
                )
        
        return {
            'average_delivery_time': sum(delivery_times) / len(delivery_times) if delivery_times else 0,
            '95th_percentile_delivery_time': self._calculate_percentile(delivery_times, 95),
            'success_rate': (
                (self.metrics['sent'].sum() - self.metrics['failed'].sum()) / 
                self.metrics['sent'].sum()
            ) if self.metrics['sent'].sum() > 0 else 0,
            'retry_rate': (
                self.metrics['retry'].sum() / self.metrics['sent'].sum()
            ) if self.metrics['sent'].sum() > 0 else 0
        }

    def _calculate_percentile(self, values: list, percentile: float) -> float:
        """Calcule le percentile des valeurs"""
        if not values:
            return 0
            
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[index]

    def get_health_status(self) -> Dict[str, Any]:
        """Obtient le statut de santé"""
        security_metrics = self.get_security_metrics()
        delivery_stats = self.get_delivery_statistics()
        
        security_score = (
            (security_metrics['suspicious_patterns'] + 
            security_metrics['malicious_content'] + 
            security_metrics['unauthorized_access']) / 3
        )
        
        delivery_score = (
            (1 - delivery_stats['success_rate']) + 
            (delivery_stats['retry_rate'])
        )
        
        status = 'healthy'
        if security_score > 0:
            status = 'warning'
        if delivery_score > 0.1:
            status = 'warning'
        if security_score > 1 or delivery_score > 0.3:
            status = 'critical'
            
        return {
            'status': status,
            'security_metrics': security_metrics,
            'delivery_stats': delivery_stats,
            'last_incident': self.security_stats['last_incident']
        }
