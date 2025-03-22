import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from utils.logger import logger

class NotificationManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.notifications')
        
        # Configuration des notifications
        self.notification_config = config.get('notifications', {
            'providers': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.polyad.com',
                    'port': 587,
                    'use_tls': True
                },
                'slack': {
                    'enabled': True,
                    'webhook_url': 'https://slack.polyad.com',
                    'channel': '#alerts'
                },
                'mobile': {
                    'enabled': True,
                    'fcm_key': 'your-fcm-key',
                    'apns_key': 'your-apns-key'
                }
            },
            'priority_levels': {
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4
            },
            'retry_config': {
                'max_retries': 3,
                'retry_delay': 300  # en secondes
            }
        })
        
        # Historique des notifications
        self.notification_history = []
        
        # État des notifications
        self.active_notifications = {}

    def send_notification(self, 
                        user_id: str, 
                        title: str, 
                        message: str, 
                        priority: str = 'medium',
                        providers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Envoie une notification"""
        if providers is None:
            providers = ['email', 'slack', 'mobile']
            
        if priority not in self.notification_config['priority_levels']:
            priority = 'medium'
            
        notification = {
            'id': self._generate_notification_id(),
            'user_id': user_id,
            'title': title,
            'message': message,
            'priority': priority,
            'providers': providers,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Ajouter à l'historique
        self.notification_history.append(notification)
        
        # Envoyer via les fournisseurs configurés
        for provider in providers:
            if self.notification_config['providers'][provider]['enabled']:
                self._send_via_provider(notification, provider)
        
        return notification

    def _generate_notification_id(self) -> str:
        """Génère un ID unique pour la notification"""
        return f"notif_{datetime.now().isoformat()}"

    def _send_via_provider(self, notification: Dict[str, Any], provider: str) -> None:
        """Envoie une notification via un fournisseur spécifique"""
        if provider == 'email':
            self._send_email(notification)
        elif provider == 'slack':
            self._send_slack(notification)
        elif provider == 'mobile':
            self._send_mobile(notification)

    def _send_email(self, notification: Dict[str, Any]) -> None:
        """Envoie une notification par email"""
        try:
            # Implémentation spécifique selon le fournisseur d'email
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            self._retry_notification(notification)

    def _send_slack(self, notification: Dict[str, Any]) -> None:
        """Envoie une notification sur Slack"""
        try:
            # Implémentation spécifique selon le webhook Slack
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi sur Slack: {e}")
            self._retry_notification(notification)

    def _send_mobile(self, notification: Dict[str, Any]) -> None:
        """Envoie une notification mobile"""
        try:
            # Implémentation spécifique selon le fournisseur de push
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de la notification mobile: {e}")
            self._retry_notification(notification)

    def _retry_notification(self, notification: Dict[str, Any]) -> None:
        """Réessaie d'envoyer une notification"""
        if notification['id'] not in self.active_notifications:
            self.active_notifications[notification['id']] = {
                'attempts': 0,
                'last_attempt': datetime.now()
            }
            
        if self.active_notifications[notification['id']]['attempts'] < self.notification_config['retry_config']['max_retries']:
            self.active_notifications[notification['id']]['attempts'] += 1
            
            # Planifier le prochain essai
            delay = self.notification_config['retry_config']['retry_delay']
            next_attempt = datetime.now() + timedelta(seconds=delay)
            
            self.active_notifications[notification['id']]['next_attempt'] = next_attempt
            
            # Réessayer plus tard
            self.logger.info(f"Réessaie d'envoyer la notification {notification['id']} dans {delay} secondes")
        else:
            # Marquer comme échoué
            notification['status'] = 'failed'
            self.logger.error(f"Notification {notification['id']} a échoué après {self.notification_config['retry_config']['max_retries']} tentatives")

    def get_notification_history(self, 
                              user_id: Optional[str] = None, 
                              priority: Optional[str] = None, 
                              start_date: Optional[str] = None, 
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtient l'historique des notifications filtré"""
        filtered_history = self.notification_history.copy()
        
        if user_id:
            filtered_history = [n for n in filtered_history if n['user_id'] == user_id]
        
        if priority:
            filtered_history = [n for n in filtered_history if n['priority'] == priority]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_history = [n for n in filtered_history if datetime.fromisoformat(n['timestamp']) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_history = [n for n in filtered_history if datetime.fromisoformat(n['timestamp']) <= end]
        
        return filtered_history

    def get_notification_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des notifications"""
        return {
            'total_sent': len(self.notification_history),
            'by_priority': {
                priority: len([n for n in self.notification_history if n['priority'] == priority])
                for priority in self.notification_config['priority_levels'].keys()
            },
            'by_provider': {
                provider: len([n for n in self.notification_history if provider in n['providers']])
                for provider in self.notification_config['providers'].keys()
            },
            'success_rate': {
                'total': len([n for n in self.notification_history if n['status'] == 'success']),
                'percentage': (
                    len([n for n in self.notification_history if n['status'] == 'success']) / 
                    len(self.notification_history)
                ) if self.notification_history else 0
            }
        }
