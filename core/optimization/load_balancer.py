"""
Module de load balancing pour Polyad
Fournit des fonctionnalités de répartition de charge pour améliorer les performances
"""

import os
import time
import json
import random
import logging
import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from enum import Enum

# Configuration du logger
logger = logging.getLogger(__name__)

class BalancingStrategy(Enum):
    """
    Stratégies de répartition de charge
    """
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    WEIGHTED = "weighted"

class BackendStatus(Enum):
    """
    États possibles d'un backend
    """
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

class Backend:
    """
    Représente un backend dans le load balancer
    """
    
    def __init__(self, id: str, url: str, weight: int = 1, max_connections: int = 100):
        """
        Initialise un backend
        
        Args:
            id (str): Identifiant unique du backend
            url (str): URL du backend
            weight (int, optional): Poids du backend pour les stratégies pondérées. Par défaut 1
            max_connections (int, optional): Nombre maximum de connexions. Par défaut 100
        """
        self.id = id
        self.url = url
        self.weight = weight
        self.max_connections = max_connections
        self.status = BackendStatus.ONLINE
        self.current_connections = 0
        self.total_connections = 0
        self.failed_connections = 0
        self.total_response_time = 0
        self.avg_response_time = 0
        self.last_health_check = 0
        self.health_check_failures = 0
        self.health_check_successes = 0
    
    def start_connection(self) -> bool:
        """
        Démarre une connexion sur ce backend
        
        Returns:
            bool: True si la connexion a pu être établie, False sinon
        """
        if self.status != BackendStatus.ONLINE:
            return False
        
        if self.current_connections >= self.max_connections:
            return False
        
        self.current_connections += 1
        self.total_connections += 1
        return True
    
    def end_connection(self, response_time: float = 0, success: bool = True) -> None:
        """
        Termine une connexion sur ce backend
        
        Args:
            response_time (float, optional): Temps de réponse en secondes. Par défaut 0
            success (bool, optional): Si la connexion a réussi. Par défaut True
        """
        if self.current_connections > 0:
            self.current_connections -= 1
        
        if not success:
            self.failed_connections += 1
        
        if response_time > 0:
            self.total_response_time += response_time
            self.avg_response_time = self.total_response_time / self.total_connections
    
    def update_health_check(self, success: bool) -> None:
        """
        Met à jour l'état de santé du backend
        
        Args:
            success (bool): Si la vérification de santé a réussi
        """
        self.last_health_check = time.time()
        
        if success:
            self.health_check_successes += 1
            self.health_check_failures = 0
            
            if self.status == BackendStatus.DEGRADED and self.health_check_successes >= 3:
                self.status = BackendStatus.ONLINE
                logger.info(f"Backend {self.id} est passé de DEGRADED à ONLINE après 3 vérifications de santé réussies")
        else:
            self.health_check_failures += 1
            self.health_check_successes = 0
            
            if self.status == BackendStatus.ONLINE and self.health_check_failures >= 3:
                self.status = BackendStatus.DEGRADED
                logger.warning(f"Backend {self.id} est passé de ONLINE à DEGRADED après 3 échecs de vérification de santé")
            
            if self.status == BackendStatus.DEGRADED and self.health_check_failures >= 5:
                self.status = BackendStatus.OFFLINE
                logger.error(f"Backend {self.id} est passé de DEGRADED à OFFLINE après 5 échecs de vérification de santé")
    
    def set_status(self, status: BackendStatus) -> None:
        """
        Définit manuellement le statut du backend
        
        Args:
            status (BackendStatus): Nouveau statut
        """
        old_status = self.status
        self.status = status
        logger.info(f"Backend {self.id} est passé de {old_status.value} à {status.value}")
    
    def get_load(self) -> float:
        """
        Calcule la charge actuelle du backend
        
        Returns:
            float: Charge entre 0 et 1
        """
        if self.max_connections <= 0:
            return 1.0
        
        return self.current_connections / self.max_connections
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du backend
        
        Returns:
            Dict[str, Any]: Statistiques du backend
        """
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status.value,
            'weight': self.weight,
            'current_connections': self.current_connections,
            'max_connections': self.max_connections,
            'total_connections': self.total_connections,
            'failed_connections': self.failed_connections,
            'avg_response_time': self.avg_response_time,
            'load': self.get_load(),
            'last_health_check': self.last_health_check,
            'health_check_failures': self.health_check_failures,
            'health_check_successes': self.health_check_successes
        }


class LoadBalancer:
    """
    Gestionnaire de répartition de charge
    """
    
    def __init__(
        self,
        strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN,
        health_check_interval: int = 60,
        health_check_timeout: int = 5
    ):
        """
        Initialise le load balancer
        
        Args:
            strategy (BalancingStrategy, optional): Stratégie de répartition. Par défaut ROUND_ROBIN
            health_check_interval (int, optional): Intervalle de vérification de santé en secondes. Par défaut 60
            health_check_timeout (int, optional): Timeout de vérification de santé en secondes. Par défaut 5
        """
        self.backends: Dict[str, Backend] = {}
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.health_check_task = None
        self.round_robin_index = 0
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0
        }
    
    def add_backend(self, id: str, url: str, weight: int = 1, max_connections: int = 100) -> Backend:
        """
        Ajoute un backend au load balancer
        
        Args:
            id (str): Identifiant unique du backend
            url (str): URL du backend
            weight (int, optional): Poids du backend pour les stratégies pondérées. Par défaut 1
            max_connections (int, optional): Nombre maximum de connexions. Par défaut 100
            
        Returns:
            Backend: Instance du backend ajouté
        """
        backend = Backend(id, url, weight, max_connections)
        self.backends[id] = backend
        logger.info(f"Backend ajouté: {id} ({url})")
        return backend
    
    def remove_backend(self, id: str) -> bool:
        """
        Supprime un backend du load balancer
        
        Args:
            id (str): Identifiant du backend
            
        Returns:
            bool: True si le backend a été supprimé, False sinon
        """
        if id in self.backends:
            del self.backends[id]
            logger.info(f"Backend supprimé: {id}")
            return True
        return False
    
    def get_backend(self, id: str) -> Optional[Backend]:
        """
        Récupère un backend par son identifiant
        
        Args:
            id (str): Identifiant du backend
            
        Returns:
            Optional[Backend]: Instance du backend ou None si non trouvé
        """
        return self.backends.get(id)
    
    def get_all_backends(self) -> List[Backend]:
        """
        Récupère tous les backends
        
        Returns:
            List[Backend]: Liste des backends
        """
        return list(self.backends.values())
    
    def get_online_backends(self) -> List[Backend]:
        """
        Récupère les backends en ligne
        
        Returns:
            List[Backend]: Liste des backends en ligne
        """
        return [b for b in self.backends.values() if b.status == BackendStatus.ONLINE]
    
    def set_strategy(self, strategy: BalancingStrategy) -> None:
        """
        Définit la stratégie de répartition
        
        Args:
            strategy (BalancingStrategy): Nouvelle stratégie
        """
        self.strategy = strategy
        logger.info(f"Stratégie de répartition définie: {strategy.value}")
    
    async def start_health_checks(self) -> None:
        """
        Démarre les vérifications de santé périodiques
        """
        if self.health_check_task is None:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"Vérifications de santé démarrées (intervalle: {self.health_check_interval}s)")
    
    async def stop_health_checks(self) -> None:
        """
        Arrête les vérifications de santé périodiques
        """
        if self.health_check_task is not None:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
            logger.info("Vérifications de santé arrêtées")
    
    async def _health_check_loop(self) -> None:
        """
        Boucle de vérification de santé périodique
        """
        try:
            while True:
                await self._check_all_backends_health()
                await asyncio.sleep(self.health_check_interval)
        except asyncio.CancelledError:
            logger.info("Boucle de vérification de santé annulée")
        except Exception as e:
            logger.error(f"Erreur dans la boucle de vérification de santé: {e}")
    
    async def _check_all_backends_health(self) -> None:
        """
        Vérifie la santé de tous les backends
        """
        for backend_id, backend in self.backends.items():
            if backend.status != BackendStatus.MAINTENANCE:
                success = await self._check_backend_health(backend)
                backend.update_health_check(success)
    
    async def _check_backend_health(self, backend: Backend) -> bool:
        """
        Vérifie la santé d'un backend
        
        Args:
            backend (Backend): Backend à vérifier
            
        Returns:
            bool: True si le backend est en bonne santé, False sinon
        """
        # Simuler une vérification de santé
        # Dans une implémentation réelle, cela ferait une requête HTTP au backend
        try:
            # Simuler un délai et un résultat aléatoire pour la démonstration
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # 90% de chance de succès pour les backends en ligne
            # 50% de chance de succès pour les backends dégradés
            # 10% de chance de succès pour les backends hors ligne
            success_chance = {
                BackendStatus.ONLINE: 0.9,
                BackendStatus.DEGRADED: 0.5,
                BackendStatus.OFFLINE: 0.1,
                BackendStatus.MAINTENANCE: 0
            }.get(backend.status, 0)
            
            success = random.random() < success_chance
            
            if success:
                logger.debug(f"Vérification de santé réussie pour le backend {backend.id}")
            else:
                logger.warning(f"Échec de la vérification de santé pour le backend {backend.id}")
            
            return success
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de santé du backend {backend.id}: {e}")
            return False
    
    def select_backend(self, request_info: Optional[Dict[str, Any]] = None) -> Optional[Backend]:
        """
        Sélectionne un backend selon la stratégie configurée
        
        Args:
            request_info (Optional[Dict[str, Any]], optional): Informations sur la requête. Par défaut None
            
        Returns:
            Optional[Backend]: Backend sélectionné ou None si aucun backend disponible
        """
        online_backends = self.get_online_backends()
        
        if not online_backends:
            logger.warning("Aucun backend en ligne disponible")
            return None
        
        if self.strategy == BalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(online_backends)
        elif self.strategy == BalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(online_backends)
        elif self.strategy == BalancingStrategy.LEAST_RESPONSE_TIME:
            return self._select_least_response_time(online_backends)
        elif self.strategy == BalancingStrategy.IP_HASH:
            return self._select_ip_hash(online_backends, request_info)
        elif self.strategy == BalancingStrategy.RANDOM:
            return self._select_random(online_backends)
        elif self.strategy == BalancingStrategy.WEIGHTED:
            return self._select_weighted(online_backends)
        else:
            # Par défaut, utiliser round robin
            return self._select_round_robin(online_backends)
    
    def _select_round_robin(self, backends: List[Backend]) -> Backend:
        """
        Sélectionne un backend avec la stratégie round robin
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        # Incrémenter l'index et le limiter à la taille de la liste
        self.round_robin_index = (self.round_robin_index + 1) % len(backends)
        return backends[self.round_robin_index]
    
    def _select_least_connections(self, backends: List[Backend]) -> Backend:
        """
        Sélectionne le backend avec le moins de connexions actives
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        return min(backends, key=lambda b: b.current_connections)
    
    def _select_least_response_time(self, backends: List[Backend]) -> Backend:
        """
        Sélectionne le backend avec le temps de réponse moyen le plus bas
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        # Filtrer les backends qui ont déjà reçu des requêtes
        backends_with_requests = [b for b in backends if b.total_connections > 0]
        
        if not backends_with_requests:
            # Si aucun backend n'a encore reçu de requête, utiliser round robin
            return self._select_round_robin(backends)
        
        return min(backends_with_requests, key=lambda b: b.avg_response_time)
    
    def _select_ip_hash(self, backends: List[Backend], request_info: Optional[Dict[str, Any]]) -> Backend:
        """
        Sélectionne un backend en fonction du hachage de l'IP client
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            request_info (Optional[Dict[str, Any]]): Informations sur la requête
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        # Utiliser l'IP du client si disponible, sinon utiliser une valeur par défaut
        client_ip = request_info.get('client_ip', '127.0.0.1') if request_info else '127.0.0.1'
        
        # Calculer un hachage de l'IP
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        
        # Utiliser le hachage pour sélectionner un backend
        index = hash_value % len(backends)
        return backends[index]
    
    def _select_random(self, backends: List[Backend]) -> Backend:
        """
        Sélectionne un backend aléatoirement
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        return random.choice(backends)
    
    def _select_weighted(self, backends: List[Backend]) -> Backend:
        """
        Sélectionne un backend en fonction de son poids
        
        Args:
            backends (List[Backend]): Liste des backends disponibles
            
        Returns:
            Backend: Backend sélectionné
        """
        if not backends:
            raise ValueError("Aucun backend disponible")
        
        # Créer une liste pondérée où chaque backend apparaît proportionnellement à son poids
        weighted_backends = []
        for backend in backends:
            weighted_backends.extend([backend] * backend.weight)
        
        return random.choice(weighted_backends)
    
    async def handle_request(self, request_info: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Backend], float]:
        """
        Gère une requête en sélectionnant un backend et en mesurant le temps de réponse
        
        Args:
            request_info (Optional[Dict[str, Any]], optional): Informations sur la requête. Par défaut None
            
        Returns:
            Tuple[Optional[Backend], float]: Backend utilisé et temps de réponse
        """
        self.stats['total_requests'] += 1
        
        # Sélectionner un backend
        backend = self.select_backend(request_info)
        
        if backend is None:
            self.stats['failed_requests'] += 1
            return None, 0
        
        # Démarrer une connexion
        if not backend.start_connection():
            self.stats['failed_requests'] += 1
            return None, 0
        
        start_time = time.time()
        success = True
        
        try:
            # Simuler le traitement de la requête
            # Dans une implémentation réelle, cela transmettrait la requête au backend
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Simuler un échec aléatoire (5% de chance)
            if random.random() < 0.05:
                raise Exception("Erreur simulée")
            
            self.stats['successful_requests'] += 1
            return backend, time.time() - start_time
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête sur le backend {backend.id}: {e}")
            success = False
            self.stats['failed_requests'] += 1
            return None, 0
        finally:
            # Terminer la connexion
            response_time = time.time() - start_time
            backend.end_connection(response_time, success)
            
            # Mettre à jour le temps de réponse moyen global
            total_successful = self.stats['successful_requests']
            if total_successful > 0:
                self.stats['avg_response_time'] = (
                    (self.stats['avg_response_time'] * (total_successful - 1)) + response_time
                ) / total_successful
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du load balancer
        
        Returns:
            Dict[str, Any]: Statistiques du load balancer
        """
        return {
            **self.stats,
            'strategy': self.strategy.value,
            'backends': {id: backend.get_stats() for id, backend in self.backends.items()},
            'online_backends': len(self.get_online_backends()),
            'total_backends': len(self.backends),
            'success_rate': self.stats['successful_requests'] / self.stats['total_requests'] if self.stats['total_requests'] > 0 else 0
        }
