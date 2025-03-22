import logging
from typing import Dict, Any, Optional, Union
import time
from datetime import datetime, timedelta
from utils.logger import logger

class RateLimiter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.rate_limiter')
        
        # Configuration du rate limiting
        self.rate_limit_config = config.get('rate_limit', {
            'default_limits': {
                'requests_per_minute': 1000,
                'window_size': 60,  # en secondes
                'block_duration': 300  # en secondes
            },
            'ip_limits': {
                'requests_per_minute': 5000,
                'window_size': 60,
                'block_duration': 600
            },
            'user_limits': {
                'requests_per_minute': 100,
                'window_size': 60,
                'block_duration': 300
            },
            'burst_config': {
                'enabled': True,
                'max_burst': 10,
                'recovery_time': 30  # en secondes
            },
            'whitelist': []
        })
        
        # État du rate limiting
        self.rate_limits = {
            'default': {},
            'ip': {},
            'user': {}
        }
        
        # État des bursts
        self.burst_state = {}
        
        # Whitelist
        self.whitelist = set(self.rate_limit_config['whitelist'])

    def check_rate_limit(self, 
                        identifier: str, 
                        limit_type: str = 'default',
                        burst: bool = False) -> bool:
        """Vérifie les limites de taux pour un identifiant"""
        if identifier in self.whitelist:
            return True
            
        if limit_type not in self.rate_limits:
            raise ValueError(f"Type de limite non supporté: {limit_type}")
            
        if identifier not in self.rate_limits[limit_type]:
            self.rate_limits[limit_type][identifier] = {
                'count': 0,
                'last_reset': time.time(),
                'blocked_until': 0
            }
        
        current_time = time.time()
        window_start = current_time - self.rate_limit_config[limit_type]['window_size']
        
        # Réinitialiser le compteur si nécessaire
        if self.rate_limits[limit_type][identifier]['last_reset'] < window_start:
            self.rate_limits[limit_type][identifier] = {
                'count': 0,
                'last_reset': current_time,
                'blocked_until': 0
            }
        
        # Vérifier si l'identifiant est bloqué
        if self.rate_limits[limit_type][identifier]['blocked_until'] > current_time:
            return False
            
        # Gérer le burst si activé
        if burst and self.rate_limit_config['burst_config']['enabled']:
            return self._handle_burst(identifier, limit_type)
            
        # Vérifier la limite
        if self.rate_limits[limit_type][identifier]['count'] >= self.rate_limit_config[limit_type]['requests_per_minute']:
            self._block_identifier(identifier, limit_type)
            return False
            
        self.rate_limits[limit_type][identifier]['count'] += 1
        return True

    def _handle_burst(self, identifier: str, limit_type: str) -> bool:
        """Gère les bursts de requêtes"""
        if identifier not in self.burst_state:
            self.burst_state[identifier] = {
                'remaining': self.rate_limit_config['burst_config']['max_burst'],
                'last_burst': time.time()
            }
        
        current_time = time.time()
        
        # Réinitialiser le burst si le temps de récupération est écoulé
        if current_time - self.burst_state[identifier]['last_burst'] > self.rate_limit_config['burst_config']['recovery_time']:
            self.burst_state[identifier] = {
                'remaining': self.rate_limit_config['burst_config']['max_burst'],
                'last_burst': current_time
            }
        
        # Vérifier si le burst est disponible
        if self.burst_state[identifier]['remaining'] <= 0:
            return False
            
        # Utiliser un burst
        self.burst_state[identifier]['remaining'] -= 1
        self.burst_state[identifier]['last_burst'] = current_time
        
        return True

    def _block_identifier(self, identifier: str, limit_type: str) -> None:
        """Bloque un identifiant"""
        block_time = time.time() + self.rate_limit_config[limit_type]['block_duration']
        self.rate_limits[limit_type][identifier]['blocked_until'] = block_time
        self.logger.warning(f"{limit_type.capitalize()} {identifier} bloqué pour {self.rate_limit_config[limit_type]['block_duration']} secondes")

    def get_rate_limit_status(self, identifier: str, limit_type: str = 'default') -> Dict[str, Any]:
        """Obtient le statut du rate limiting pour un identifiant"""
        if identifier not in self.rate_limits[limit_type]:
            return {
                'limit_type': limit_type,
                'identifier': identifier,
                'current_count': 0,
                'limit': self.rate_limit_config[limit_type]['requests_per_minute'],
                'blocked_until': 0,
                'burst_remaining': self.rate_limit_config['burst_config']['max_burst']
            }
            
        return {
            'limit_type': limit_type,
            'identifier': identifier,
            'current_count': self.rate_limits[limit_type][identifier]['count'],
            'limit': self.rate_limit_config[limit_type]['requests_per_minute'],
            'blocked_until': self.rate_limits[limit_type][identifier]['blocked_until'],
            'burst_remaining': self.burst_state.get(identifier, {}).get('remaining', 0)
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Obtient le statut global du rate limiting"""
        return {
            'total_limits': {
                'default': len(self.rate_limits['default']),
                'ip': len(self.rate_limits['ip']),
                'user': len(self.rate_limits['user'])
            },
            'blocked': {
                'default': len([i for i in self.rate_limits['default'].values() if i['blocked_until'] > time.time()]),
                'ip': len([i for i in self.rate_limits['ip'].values() if i['blocked_until'] > time.time()]),
                'user': len([i for i in self.rate_limits['user'].values() if i['blocked_until'] > time.time()])
            },
            'whitelist': list(self.whitelist),
            'burst_config': self.rate_limit_config['burst_config']
        }

    def add_to_whitelist(self, identifier: str) -> None:
        """Ajoute un identifiant à la whitelist"""
        self.whitelist.add(identifier)
        self.logger.info(f"Ajout de {identifier} à la whitelist")

    def remove_from_whitelist(self, identifier: str) -> None:
        """Supprime un identifiant de la whitelist"""
        if identifier in self.whitelist:
            self.whitelist.remove(identifier)
            self.logger.info(f"Suppression de {identifier} de la whitelist")

    def reset_limits(self, identifier: str, limit_type: str = 'default') -> None:
        """Réinitialise les limites pour un identifiant"""
        if identifier in self.rate_limits[limit_type]:
            self.rate_limits[limit_type][identifier] = {
                'count': 0,
                'last_reset': time.time(),
                'blocked_until': 0
            }
            self.logger.info(f"Réinitialisation des limites pour {identifier} ({limit_type})")
