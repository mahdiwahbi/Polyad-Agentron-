import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from utils.logger import logger

class AuditLogger:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.audit')
        
        # Configuration de l'audit
        self.audit_config = config.get('audit', {
            'log_level': 'INFO',
            'retention_days': 30,
            'max_logs': 10000,
            'log_format': 'json',
            'log_file': 'audit.log',
            'enable_db_logging': True,
            'enable_remote_logging': True,
            'remote_endpoint': 'https://audit.polyad.com'
        })
        
        # Historique des audits
        self.audit_history = []
        
        # Configuration des catégories d'audit
        self.audit_categories = {
            'authentication': ['login', 'logout', 'password_change'],
            'authorization': ['role_change', 'permission_change'],
            'data_access': ['read', 'write', 'delete'],
            'system': ['startup', 'shutdown', 'error'],
            'security': ['ip_block', 'rate_limit', 'attack_detection']
        }

    def log_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None:
        """Enregistre un événement d'audit"""
        audit_event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'category': self._get_category(event_type)
        }
        
        # Enregistrer dans le fichier
        self._log_to_file(audit_event)
        
        # Enregistrer dans la base de données
        if self.audit_config['enable_db_logging']:
            self._log_to_db(audit_event)
        
        # Enregistrer sur le serveur distant
        if self.audit_config['enable_remote_logging']:
            self._log_to_remote(audit_event)
        
        # Ajouter à l'historique
        self.audit_history.append(audit_event)
        
        # Nettoyer les logs anciens
        self._cleanup_old_logs()

    def _get_category(self, event_type: str) -> str:
        """Obtient la catégorie d'un événement"""
        for category, events in self.audit_categories.items():
            if event_type in events:
                return category
        return 'other'

    def _log_to_file(self, event: Dict[str, Any]) -> None:
        """Enregistre un événement dans le fichier"""
        with open(self.audit_config['log_file'], 'a') as f:
            if self.audit_config['log_format'] == 'json':
                f.write(json.dumps(event) + '\n')
            else:
                f.write(f"{event['timestamp']} - {event['event_type']} - {event['user_id']} - {event['details']}\n")

    def _log_to_db(self, event: Dict[str, Any]) -> None:
        """Enregistre un événement dans la base de données"""
        try:
            # Implémentation spécifique selon le type de base de données
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement dans la base de données: {e}")

    def _log_to_remote(self, event: Dict[str, Any]) -> None:
        """Enregistre un événement sur le serveur distant"""
        try:
            # Implémentation spécifique selon le endpoint distant
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement sur le serveur distant: {e}")

    def _cleanup_old_logs(self) -> None:
        """Nettoie les logs anciens"""
        cutoff_date = datetime.now() - timedelta(days=self.audit_config['retention_days'])
        
        # Nettoyer les logs du fichier
        new_logs = []
        with open(self.audit_config['log_file'], 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_date = datetime.fromisoformat(event['timestamp'])
                    if event_date >= cutoff_date:
                        new_logs.append(line)
                except:
                    continue
        
        # Écrire les logs récents
        with open(self.audit_config['log_file'], 'w') as f:
            f.writelines(new_logs)

    def get_audit_history(self, user_id: Optional[str] = None, 
                        event_type: Optional[str] = None, 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtient l'historique des audits filtré"""
        filtered_history = self.audit_history.copy()
        
        if user_id:
            filtered_history = [e for e in filtered_history if e['user_id'] == user_id]
        
        if event_type:
            filtered_history = [e for e in filtered_history if e['event_type'] == event_type]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_history = [e for e in filtered_history if datetime.fromisoformat(e['timestamp']) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_history = [e for e in filtered_history if datetime.fromisoformat(e['timestamp']) <= end]
        
        return filtered_history

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques d'audit"""
        return {
            'total_logs': len(self.audit_history),
            'categories': {
                category: len([e for e in self.audit_history if e['category'] == category])
                for category in self.audit_categories.keys()
            },
            'users': {
                user: len([e for e in self.audit_history if e['user_id'] == user])
                for user in set(e['user_id'] for e in self.audit_history)
            },
            'events': {
                event: len([e for e in self.audit_history if e['event_type'] == event])
                for event in set(e['event_type'] for e in self.audit_history)
            }
        }
