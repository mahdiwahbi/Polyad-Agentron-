"""
Module de cache distribué pour Polyad
Fournit des fonctionnalités de mise en cache pour améliorer les performances
"""

import time
import json
import hashlib
import logging
import asyncio
import functools
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

# Configuration du logger
logger = logging.getLogger(__name__)

class CacheItem:
    """
    Représente un élément dans le cache
    """
    
    def __init__(self, key: str, value: Any, ttl: int = 3600):
        """
        Initialise un élément de cache
        
        Args:
            key (str): Clé de l'élément
            value (Any): Valeur de l'élément
            ttl (int, optional): Durée de vie en secondes. Par défaut 3600 (1 heure)
        """
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """
        Vérifie si l'élément est expiré
        
        Returns:
            bool: True si l'élément est expiré, False sinon
        """
        return time.time() > (self.created_at + self.ttl)
    
    def access(self) -> Any:
        """
        Accède à l'élément et met à jour les statistiques
        
        Returns:
            Any: Valeur de l'élément
        """
        self.last_accessed = time.time()
        self.access_count += 1
        return self.value
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Récupère les métadonnées de l'élément
        
        Returns:
            Dict[str, Any]: Métadonnées de l'élément
        """
        return {
            'key': self.key,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'ttl': self.ttl,
            'expires_at': self.created_at + self.ttl,
            'is_expired': self.is_expired(),
            'age': time.time() - self.created_at,
            'type': type(self.value).__name__
        }


class MemoryCache:
    """
    Implémentation de cache en mémoire
    """
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        """
        Initialise le cache en mémoire
        
        Args:
            max_size (int, optional): Taille maximale du cache. Par défaut 1000
            cleanup_interval (int, optional): Intervalle de nettoyage en secondes. Par défaut 300 (5 minutes)
        """
        self.cache: Dict[str, CacheItem] = {}
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.cleanup_task = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    async def start_cleanup(self):
        """
        Démarre la tâche de nettoyage périodique
        """
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info(f"Tâche de nettoyage du cache démarrée (intervalle: {self.cleanup_interval}s)")
    
    async def stop_cleanup(self):
        """
        Arrête la tâche de nettoyage périodique
        """
        if self.cleanup_task is not None:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
            logger.info("Tâche de nettoyage du cache arrêtée")
    
    async def _cleanup_loop(self):
        """
        Boucle de nettoyage périodique
        """
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup()
        except asyncio.CancelledError:
            logger.info("Boucle de nettoyage du cache annulée")
        except Exception as e:
            logger.error(f"Erreur dans la boucle de nettoyage du cache: {e}")
    
    async def cleanup(self):
        """
        Nettoie les éléments expirés du cache
        """
        expired_keys = []
        
        # Identifier les éléments expirés
        for key, item in self.cache.items():
            if item.is_expired():
                expired_keys.append(key)
        
        # Supprimer les éléments expirés
        for key in expired_keys:
            del self.cache[key]
            self.stats['expirations'] += 1
        
        if expired_keys:
            logger.debug(f"Nettoyage du cache: {len(expired_keys)} éléments expirés supprimés")
    
    def _evict_if_needed(self):
        """
        Évince des éléments si le cache est plein
        """
        if len(self.cache) >= self.max_size:
            # Stratégie LRU (Least Recently Used)
            oldest_key = min(self.cache.items(), key=lambda x: x[1].last_accessed)[0]
            del self.cache[oldest_key]
            self.stats['evictions'] += 1
            logger.debug(f"Éviction du cache: élément '{oldest_key}' supprimé (LRU)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            Optional[Any]: Valeur de l'élément ou None si non trouvé
        """
        item = self.cache.get(key)
        
        if item is None:
            self.stats['misses'] += 1
            return None
        
        if item.is_expired():
            del self.cache[key]
            self.stats['expirations'] += 1
            self.stats['misses'] += 1
            return None
        
        self.stats['hits'] += 1
        return item.access()
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Définit un élément dans le cache
        
        Args:
            key (str): Clé de l'élément
            value (Any): Valeur de l'élément
            ttl (int, optional): Durée de vie en secondes. Par défaut 3600 (1 heure)
        """
        self._evict_if_needed()
        self.cache[key] = CacheItem(key, value, ttl)
        self.stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        Supprime un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            bool: True si l'élément a été supprimé, False sinon
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """
        Vide le cache
        """
        self.cache.clear()
        logger.info("Cache vidé")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        return {
            **self.stats,
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size if self.max_size > 0 else 0,
            'hit_ratio': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
        }
    
    def get_keys(self) -> List[str]:
        """
        Récupère les clés du cache
        
        Returns:
            List[str]: Liste des clés
        """
        return list(self.cache.keys())
    
    def get_item_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'un élément
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            Optional[Dict[str, Any]]: Métadonnées de l'élément ou None si non trouvé
        """
        item = self.cache.get(key)
        if item is None:
            return None
        return item.get_metadata()


class RedisCache:
    """
    Implémentation de cache utilisant Redis
    Nécessite le package aioredis
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "polyad:cache:"):
        """
        Initialise le cache Redis
        
        Args:
            redis_url (str, optional): URL de connexion Redis. Par défaut "redis://localhost:6379/0"
            prefix (str, optional): Préfixe des clés. Par défaut "polyad:cache:"
        """
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    async def initialize(self):
        """
        Initialise la connexion Redis
        
        Returns:
            bool: True si l'initialisation a réussi, False sinon
        """
        try:
            import aioredis
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            logger.info(f"Connexion Redis établie: {self.redis_url}")
            return True
        except ImportError:
            logger.error("Le package aioredis n'est pas installé. Installez-le avec 'pip install aioredis'")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Redis: {e}")
            return False
    
    async def close(self):
        """
        Ferme la connexion Redis
        """
        if self.redis is not None:
            self.redis.close()
            await self.redis.wait_closed()
            self.redis = None
            logger.info("Connexion Redis fermée")
    
    def _format_key(self, key: str) -> str:
        """
        Formate une clé avec le préfixe
        
        Args:
            key (str): Clé à formater
            
        Returns:
            str: Clé formatée
        """
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            Optional[Any]: Valeur de l'élément ou None si non trouvé
        """
        if self.redis is None:
            self.stats['misses'] += 1
            return None
        
        formatted_key = self._format_key(key)
        
        try:
            value = await self.redis.get(formatted_key)
            
            if value is None:
                self.stats['misses'] += 1
                return None
            
            # Incrémenter le compteur d'accès
            await self.redis.hincrby(f"{formatted_key}:meta", "access_count", 1)
            await self.redis.hset(f"{formatted_key}:meta", "last_accessed", str(time.time()))
            
            self.stats['hits'] += 1
            return json.loads(value)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la clé '{key}' depuis Redis: {e}")
            self.stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Définit un élément dans le cache
        
        Args:
            key (str): Clé de l'élément
            value (Any): Valeur de l'élément
            ttl (int, optional): Durée de vie en secondes. Par défaut 3600 (1 heure)
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if self.redis is None:
            return False
        
        formatted_key = self._format_key(key)
        
        try:
            # Stocker la valeur
            serialized_value = json.dumps(value)
            await self.redis.set(formatted_key, serialized_value, expire=ttl)
            
            # Stocker les métadonnées
            meta = {
                "key": key,
                "created_at": str(time.time()),
                "last_accessed": str(time.time()),
                "access_count": "0",
                "ttl": str(ttl),
                "type": type(value).__name__
            }
            
            await self.redis.hmset_dict(f"{formatted_key}:meta", meta)
            await self.redis.expire(f"{formatted_key}:meta", ttl)
            
            self.stats['sets'] += 1
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la clé '{key}' dans Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Supprime un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            bool: True si l'élément a été supprimé, False sinon
        """
        if self.redis is None:
            return False
        
        formatted_key = self._format_key(key)
        
        try:
            # Supprimer la valeur et les métadonnées
            await self.redis.delete(formatted_key, f"{formatted_key}:meta")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la clé '{key}' de Redis: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Vide le cache
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if self.redis is None:
            return False
        
        try:
            # Récupérer toutes les clés avec le préfixe
            keys = await self.redis.keys(f"{self.prefix}*")
            
            if keys:
                await self.redis.delete(*keys)
            
            logger.info(f"Cache Redis vidé: {len(keys)} clés supprimées")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache Redis: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        if self.redis is None:
            return self.stats
        
        try:
            # Récupérer des informations sur Redis
            info = await self.redis.info()
            
            # Récupérer le nombre de clés avec le préfixe
            keys = await self.redis.keys(f"{self.prefix}*")
            num_keys = len(keys) // 2  # Diviser par 2 car chaque élément a une clé de valeur et une clé de métadonnées
            
            return {
                **self.stats,
                'size': num_keys,
                'redis_memory_used': info.get('used_memory_human', 'N/A'),
                'redis_connected_clients': info.get('connected_clients', 'N/A'),
                'hit_ratio': self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques Redis: {e}")
            return self.stats


class CacheManager:
    """
    Gestionnaire de cache qui peut utiliser différentes implémentations
    """
    
    def __init__(self, implementation: str = "memory", **kwargs):
        """
        Initialise le gestionnaire de cache
        
        Args:
            implementation (str, optional): Implémentation à utiliser ("memory" ou "redis"). Par défaut "memory"
            **kwargs: Arguments supplémentaires pour l'implémentation
        """
        self.implementation = implementation
        
        if implementation == "memory":
            self.cache = MemoryCache(**kwargs)
        elif implementation == "redis":
            self.cache = RedisCache(**kwargs)
        else:
            raise ValueError(f"Implémentation de cache non prise en charge: {implementation}")
        
        logger.info(f"Gestionnaire de cache initialisé avec l'implémentation '{implementation}'")
    
    async def initialize(self):
        """
        Initialise le cache
        
        Returns:
            bool: True si l'initialisation a réussi, False sinon
        """
        if hasattr(self.cache, 'initialize'):
            return await self.cache.initialize()
        
        if hasattr(self.cache, 'start_cleanup'):
            await self.cache.start_cleanup()
        
        return True
    
    async def close(self):
        """
        Ferme le cache
        """
        if hasattr(self.cache, 'close'):
            await self.cache.close()
        
        if hasattr(self.cache, 'stop_cleanup'):
            await self.cache.stop_cleanup()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            Optional[Any]: Valeur de l'élément ou None si non trouvé
        """
        if hasattr(self.cache, 'get'):
            if asyncio.iscoroutinefunction(self.cache.get):
                return await self.cache.get(key)
            else:
                return self.cache.get(key)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Définit un élément dans le cache
        
        Args:
            key (str): Clé de l'élément
            value (Any): Valeur de l'élément
            ttl (int, optional): Durée de vie en secondes. Par défaut 3600 (1 heure)
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if hasattr(self.cache, 'set'):
            if asyncio.iscoroutinefunction(self.cache.set):
                return await self.cache.set(key, value, ttl)
            else:
                self.cache.set(key, value, ttl)
                return True
        return False
    
    async def delete(self, key: str) -> bool:
        """
        Supprime un élément du cache
        
        Args:
            key (str): Clé de l'élément
            
        Returns:
            bool: True si l'élément a été supprimé, False sinon
        """
        if hasattr(self.cache, 'delete'):
            if asyncio.iscoroutinefunction(self.cache.delete):
                return await self.cache.delete(key)
            else:
                return self.cache.delete(key)
        return False
    
    async def clear(self) -> bool:
        """
        Vide le cache
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if hasattr(self.cache, 'clear'):
            if asyncio.iscoroutinefunction(self.cache.clear):
                return await self.cache.clear()
            else:
                self.cache.clear()
                return True
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        if hasattr(self.cache, 'get_stats'):
            if asyncio.iscoroutinefunction(self.cache.get_stats):
                return await self.cache.get_stats()
            else:
                return self.cache.get_stats()
        return {}


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Décorateur pour mettre en cache le résultat d'une fonction
    
    Args:
        ttl (int, optional): Durée de vie en secondes. Par défaut 3600 (1 heure)
        key_prefix (str, optional): Préfixe pour la clé de cache. Par défaut ""
        
    Returns:
        Callable: Fonction décorée
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtenir le gestionnaire de cache
            cache_manager = args[0].cache_manager if hasattr(args[0], 'cache_manager') else None
            
            if cache_manager is None:
                # Si pas de gestionnaire de cache, exécuter la fonction normalement
                return await func(*args, **kwargs)
            
            # Générer une clé de cache basée sur la fonction et les arguments
            key_parts = [key_prefix, func.__name__]
            
            # Ajouter les arguments positionnels
            for arg in args[1:]:  # Ignorer self/cls
                key_parts.append(str(arg))
            
            # Ajouter les arguments nommés (triés par nom)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            # Joindre les parties et hacher pour obtenir une clé
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Essayer de récupérer depuis le cache
            cached_value = await cache_manager.get(key)
            
            if cached_value is not None:
                return cached_value
            
            # Exécuter la fonction et mettre en cache le résultat
            result = await func(*args, **kwargs)
            await cache_manager.set(key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator
