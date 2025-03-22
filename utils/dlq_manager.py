import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta
from utils.logger import logger

class DLQManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.dlq')
        
        # Configuration de la DLQ
        self.dlq_config = config.get('dlq', {
            'max_messages': 10000,
            'retention_days': 7,
            'cleanup_interval': 3600,  # en secondes
            'retry_config': {
                'max_retries': 3,
                'retry_delay': 300,  # en secondes
                'backoff_factor': 1.5
            },
            'storage': {
                'type': 'file',
                'path': 'dlq',
                'max_size_mb': 100
            }
        })
        
        # État de la DLQ
        self.messages = {}
        self.retry_queue = {}
        
        # Statistiques
        self.stats = {
            'total_messages': 0,
            'processed': 0,
            'failed': 0,
            'retried': 0,
            'current_size': 0
        }

    def send_to_dlq(self, message: Dict[str, Any]) -> str:
        """Envoie un message dans la DLQ"""
        message_id = self._generate_message_id()
        
        # Vérifier la taille maximale
        message_size = len(json.dumps(message).encode('utf-8'))
        if self.stats['current_size'] + message_size > self.dlq_config['storage']['max_size_mb'] * 1024 * 1024:
            self._cleanup_old_messages()
        
        # Ajouter le message
        self.messages[message_id] = {
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'retries': 0,
            'last_attempt': None,
            'status': 'pending'
        }
        
        self.stats['total_messages'] += 1
        self.stats['current_size'] += message_size
        
        return message_id

    def get_from_dlq(self) -> Optional[Dict[str, Any]]:
        """Obtient un message de la DLQ"""
        for message_id, message in self.messages.items():
            if message['status'] == 'pending':
                self.messages[message_id]['status'] = 'processing'
                return message['message']
        return None

    def process_message(self, message_id: str, success: bool) -> None:
        """Traite un message de la DLQ"""
        if message_id not in self.messages:
            return
            
        message = self.messages[message_id]
        
        if success:
            message['status'] = 'processed'
            self.stats['processed'] += 1
        else:
            message['status'] = 'failed'
            self.stats['failed'] += 1
            
            # Gérer les retries
            if message['retries'] < self.dlq_config['retry_config']['max_retries']:
                self._schedule_retry(message_id)
            else:
                message['status'] = 'abandoned'

    def _schedule_retry(self, message_id: str) -> None:
        """Planifie un retry pour un message"""
        message = self.messages[message_id]
        
        # Calculer le délai avec backoff
        retry_delay = self.dlq_config['retry_config']['retry_delay'] * (
            self.dlq_config['retry_config']['backoff_factor'] ** message['retries']
        )
        
        self.retry_queue[message_id] = {
            'retry_time': time.time() + retry_delay,
            'attempts': message['retries'] + 1
        }
        
        message['retries'] += 1
        self.stats['retried'] += 1

    def _cleanup_old_messages(self) -> None:
        """Nettoie les messages anciens"""
        cutoff_date = datetime.now() - timedelta(days=self.dlq_config['retention_days'])
        
        # Nettoyer les messages anciens
        for message_id in list(self.messages.keys()):
            message = self.messages[message_id]
            message_date = datetime.fromisoformat(message['timestamp'])
            
            if message_date < cutoff_date:
                self._delete_message(message_id)

    def _delete_message(self, message_id: str) -> None:
        """Supprime un message"""
        if message_id in self.messages:
            message_size = len(json.dumps(self.messages[message_id]['message']).encode('utf-8'))
            self.stats['current_size'] -= message_size
            del self.messages[message_id]
            
        if message_id in self.retry_queue:
            del self.retry_queue[message_id]

    def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le statut d'un message"""
        if message_id in self.messages:
            return {
                'id': message_id,
                'status': self.messages[message_id]['status'],
                'retries': self.messages[message_id]['retries'],
                'last_attempt': self.messages[message_id]['last_attempt']
            }
        return None

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de la DLQ"""
        return {
            'total_messages': self.stats['total_messages'],
            'processed': self.stats['processed'],
            'failed': self.stats['failed'],
            'retried': self.stats['retried'],
            'current_size': self.stats['current_size'],
            'pending': len([m for m in self.messages.values() if m['status'] == 'pending']),
            'processing': len([m for m in self.messages.values() if m['status'] == 'processing']),
            'failed': len([m for m in self.messages.values() if m['status'] == 'failed']),
            'abandoned': len([m for m in self.messages.values() if m['status'] == 'abandoned'])
        }

    def _generate_message_id(self) -> str:
        """Génère un ID unique pour un message"""
        return f"dlq_{datetime.now().isoformat()}"

    def get_retry_queue(self) -> List[Dict[str, Any]]:
        """Obtient la file d'attente des retries"""
        return [
            {
                'message_id': message_id,
                'retry_time': retry_data['retry_time'],
                'attempts': retry_data['attempts']
            }
            for message_id, retry_data in self.retry_queue.items()
        ]

    def process_retry_queue(self) -> None:
        """Traite la file d'attente des retries"""
        current_time = time.time()
        
        for message_id, retry_data in list(self.retry_queue.items()):
            if retry_data['retry_time'] <= current_time:
                message = self.messages[message_id]
                message['status'] = 'pending'
                del self.retry_queue[message_id]
