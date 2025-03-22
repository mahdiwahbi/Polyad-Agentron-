import logging
from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta
from utils.logger import logger

class AttackProtection:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.security.attack')
        
        # Configuration de protection
        self.protection_config = config.get('attack_protection', {
            'rate_limit': {
                'requests_per_minute': 1000,
                'window_size': 60,  # en secondes
                'block_duration': 300  # en secondes
            },
            'ip_blocklist': {
                'max_attempts': 5,
                'block_duration': 3600  # en secondes
            },
            'ddos_protection': {
                'threshold': 10000,
                'window_size': 60,  # en secondes
                'block_duration': 3600  # en secondes
            },
            'sql_injection_protection': True,
            'xss_protection': True,
            'csrf_protection': True
        })
        
        # État de protection
        self.rate_limits = {}
        self.blocked_ips = {}
        self.ddos_detection = {}
        
        # Historique des attaques
        self.attack_history = []

    def check_rate_limit(self, client_id: str) -> bool:
        """Vérifie les limites de taux pour un client"""
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {
                'count': 0,
                'last_reset': time.time()
            }
        
        current_time = time.time()
        window_start = current_time - self.protection_config['rate_limit']['window_size']
        
        # Réinitialiser le compteur si nécessaire
        if self.rate_limits[client_id]['last_reset'] < window_start:
            self.rate_limits[client_id] = {
                'count': 0,
                'last_reset': current_time
            }
        
        # Vérifier la limite
        if self.rate_limits[client_id]['count'] >= self.protection_config['rate_limit']['requests_per_minute']:
            self._block_client(client_id)
            return False
            
        self.rate_limits[client_id]['count'] += 1
        return True

    def check_ip_blocklist(self, ip_address: str) -> bool:
        """Vérifie si une IP est bloquée"""
        if ip_address in self.blocked_ips:
            if time.time() < self.blocked_ips[ip_address]['unblock_time']:
                return False
            del self.blocked_ips[ip_address]
        
        return True

    def check_ddos(self, request_count: int) -> bool:
        """Vérifie les signes d'attaque DDoS"""
        current_time = time.time()
        window_start = current_time - self.protection_config['ddos_protection']['window_size']
        
        if window_start not in self.ddos_detection:
            self.ddos_detection[window_start] = {
                'count': 0,
                'last_reset': current_time
            }
        
        self.ddos_detection[window_start]['count'] += request_count
        
        if self.ddos_detection[window_start]['count'] > self.protection_config['ddos_protection']['threshold']:
            self.logger.warning("Détection d'attaque DDoS")
            return False
            
        return True

    def check_sql_injection(self, input_data: str) -> bool:
        """Vérifie les tentatives d'injection SQL"""
        if not self.protection_config['sql_injection_protection']:
            return True
            
        patterns = [
            r"\b(SELECT|UPDATE|DELETE|INSERT|DROP)\b",
            r"\b(UNION|ALL|SELECT)\b",
            r"\b(SELECT.*FROM)\b",
            r"\b(UPDATE.*SET)\b",
            r"\b(DELETE.*FROM)\b",
            r"\b(INSERT.*INTO)\b",
            r"\b(DROP.*TABLE)\b"
        ]
        
        for pattern in patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                self._log_attack('sql_injection', input_data)
                return False
                
        return True

    def check_xss(self, input_data: str) -> bool:
        """Vérifie les tentatives d'XSS"""
        if not self.protection_config['xss_protection']:
            return True
            
        patterns = [
            r"<script.*?>.*?</script>",
            r"on\w+=["'].*?['"]",
            r"javascript:[\s\S]*",
            r"vbscript:[\s\S]*",
            r"data:[\s\S]*",
            r"base64:[\s\S]*"
        ]
        
        for pattern in patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                self._log_attack('xss', input_data)
                return False
                
        return True

    def check_csrf(self, token: str, session_token: str) -> bool:
        """Vérifie la protection CSRF"""
        if not self.protection_config['csrf_protection']:
            return True
            
        return token == session_token

    def _block_client(self, client_id: str) -> None:
        """Bloque un client"""
        block_time = time.time() + self.protection_config['rate_limit']['block_duration']
        self.blocked_ips[client_id] = {
            'block_time': block_time,
            'unblock_time': block_time + self.protection_config['rate_limit']['block_duration']
        }
        self.logger.warning(f"Client {client_id} bloqué pour {self.protection_config['rate_limit']['block_duration']} secondes")

    def _log_attack(self, attack_type: str, details: str) -> None:
        """Enregistre une attaque"""
        self.attack_history.append({
            'type': attack_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })
        self.logger.warning(f"Attaque détectée: {attack_type} - {details}")

    def get_attack_history(self) -> list:
        """Obtient l'historique des attaques"""
        return self.attack_history.copy()

    def get_protection_status(self) -> Dict[str, Any]:
        """Obtient le statut de la protection"""
        return {
            'rate_limit': {
                'current': len(self.rate_limits),
                'blocked': len([c for c in self.rate_limits.values() if c['count'] >= self.protection_config['rate_limit']['requests_per_minute']])
            },
            'ip_blocklist': {
                'current': len(self.blocked_ips),
                'blocked': len([ip for ip in self.blocked_ips.values() if time.time() < ip['unblock_time']])
            },
            'ddos': {
                'current': len(self.ddos_detection),
                'detected': len([d for d in self.ddos_detection.values() if d['count'] > self.protection_config['ddos_protection']['threshold']])
            },
            'attacks': {
                'total': len(self.attack_history),
                'last_attack': self.attack_history[-1]['timestamp'] if self.attack_history else None
            }
        }
