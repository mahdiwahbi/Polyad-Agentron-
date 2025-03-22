from typing import Dict, Any, Optional, Union
import logging
import asyncio
import time
import redis
from functools import lru_cache
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialise le gestionnaire de cache
        
        Args:
            config (Dict[str, Any]): Configuration du cache
        """
        self.config = config
        self.logger = logging.getLogger('polyad.cache')
        
        # Configuration du cache
        self.max_size = config.get('cache_size', 1024 * 1024 * 1024)  # 1GB par défaut
        self.ttl = config.get('cache_ttl', 3600)  # 1 heure par défaut
        self.cleanup_interval = config.get('cache_cleanup_interval', 300)  # 5 minutes par défaut
        
        # État du cache
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None
        self.last_cleanup_time = time.time()
        
        # Initialiser les caches
        self._initialize_caches()

    def _initialize_caches(self) -> None:
        """Initialise les caches"""
        # Cache en mémoire
        self.memory_cache = {}
        
        # Cache Redis
        self.redis_client = redis.Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            db=self.config.get('redis_db', 0),
            decode_responses=True
        )
        
        # Cache LRU
        self.lru_cache = lru_cache(maxsize=self.config.get('lru_cache_size', 1000))

    async def initialize(self) -> bool:
        """Initialise le gestionnaire de cache"""
        try:
            # Tester la connexion Redis
            await self._test_redis_connection()
            
            self.logger.info("Gestionnaire de cache initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Échec de l'initialisation: {e}")
            return False

    async def _test_redis_connection(self) -> None:
        """Teste la connexion Redis"""
        try:
            self.redis_client.ping()
            self.logger.info("Connexion Redis établie")
        except Exception as e:
            self.logger.error(f"Erreur de connexion Redis: {e}")
            raise

    async def start(self) -> None:
        """Démarre le gestionnaire de cache"""
        if self.is_running:
            return
            
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_cache())
        
    async def stop(self) -> None:
        """Arrête le gestionnaire de cache"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_cache(self) -> None:
        """Nettoie le cache périodiquement"""
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_cleanup_time >= self.cleanup_interval:
                    self._cleanup_memory_cache()
                    await self._cleanup_redis_cache()
                    self.last_cleanup_time = current_time
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors du nettoyage du cache: {e}")
                await asyncio.sleep(5)

    def _cleanup_memory_cache(self) -> None:
        """Nettoie le cache en mémoire"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, timestamp) in self.memory_cache.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.memory_cache[key]
            
        self.logger.info(f"Nettoyage du cache en mémoire: {len(expired_keys)} entrées expirées")

    async def _cleanup_redis_cache(self) -> None:
        """Nettoie le cache Redis"""
        try:
            # Supprimer les clés expirées
            expired_keys = []
            for key in self.redis_client.keys():
                if self.redis_client.ttl(key) == -2:  # Clé expirée
                    expired_keys.append(key)
                    
            if expired_keys:
                self.redis_client.delete(*expired_keys)
                self.logger.info(f"Nettoyage Redis: {len(expired_keys)} entrées expirées")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage Redis: {e}")

    async def get(self, key: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Obtient une valeur du cache avec déchiffrement si nécessaire
        
        Args:
            key (str): Clé du cache
            
        Returns:
            Optional[Union[str, Dict[str, Any]]]: Valeur du cache ou None si non trouvée
        """
        try:
            # Vérifier le cache LRU
            cached_value = self.lru_cache.get(key)
            if cached_value is not None:
                return await self._decrypt_sensitive_data(cached_value)
            
            # Vérifier le cache en mémoire
            if key in self.memory_cache:
                value, timestamp = self.memory_cache[key]
                if time.time() - timestamp <= self.ttl:
                    return await self._decrypt_sensitive_data(value)
                del self.memory_cache[key]
            
            # Vérifier Redis
            value = self.redis_client.get(key)
            if value is not None:
                return await self._decrypt_sensitive_data(value)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du cache: {e}")
            return None

    async def set(self, key: str, value: Union[str, Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """
        Définit une valeur dans le cache avec chiffrement si nécessaire
        
        Args:
            key (str): Clé du cache
            value (Union[str, Dict[str, Any]]): Valeur à stocker
            ttl (Optional[int]): Temps de vie en secondes (None pour utiliser la valeur par défaut)
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Chiffrer les données sensibles
            if isinstance(value, dict) and 'sensitive' in value:
                encrypted_value = await self._encrypt_sensitive_data(value)
            else:
                encrypted_value = value
            
            # Stocker dans le cache en mémoire
            self.memory_cache[key] = (encrypted_value, time.time())
            
            # Stocker dans Redis
            self.redis_client.setex(key, ttl or self.ttl, encrypted_value)
            
            # Mettre à jour le cache LRU
            self.lru_cache(key)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture dans le cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Supprime une entrée du cache
        
        Args:
            key (str): Clé du cache à supprimer
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Supprimer du cache en mémoire
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Supprimer de Redis
            self.redis_client.delete(key)
            
            # Supprimer du cache LRU
            if key in self.lru_cache:
                del self.lru_cache[key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du cache: {e}")
            return False

    async def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> str:
        """
        Chiffre les données sensibles
        
        Args:
            data (Dict[str, Any]): Données à chiffrer
            
        Returns:
            str: Données chiffrées encodées en base64
        """
        if not isinstance(data, dict) or 'sensitive' not in data:
            return data
            
        encryption_manager = EncryptionManager(self.config['security'])
        return encryption_manager.encrypt(data['sensitive'])

    async def _decrypt_sensitive_data(self, data: str) -> Union[str, Dict[str, Any]]:
        """
        Déchiffre les données sensibles si nécessaire
        
        Args:
            data (str): Données à déchiffrer
            
        Returns:
            Union[str, Dict[str, Any]]: Données déchiffrées
        """
        try:
            encryption_manager = EncryptionManager(self.config['security'])
            return encryption_manager.decrypt(data)
            
        except Exception:
            # Si déchiffrement échoue, retourne les données originales
            return data

    async def cleanup(self) -> bool:
        """
        Nettoie le cache en supprimant les entrées expirées
        
        Returns:
            bool: True si le nettoyage a réussi
        """
        try:
            # Nettoyer le cache en mémoire
            current_time = time.time()
            keys_to_delete = []
            for key, (value, timestamp) in self.memory_cache.items():
                if current_time - timestamp > self.ttl:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.memory_cache[key]
                self.lru_cache.remove(key)
            
            # Nettoyer Redis
            if self.redis_client:
                keys = self.redis_client.keys('*')
                for key in keys:
                    if not self.redis_client.exists(key):
                        self.redis_client.delete(key)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage: {e}")
            return False

    async def close(self) -> None:
        """
        Ferme proprement le cache
        """
        try:
            # Fermer la connexion Redis
            if self.redis_client:
                self.redis_client.close()
            
            # Nettoyer le cache en mémoire
            self.memory_cache.clear()
            self.lru_cache.clear()
            
            self.logger.info("Cache fermé proprement")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la fermeture du cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques du cache
        
        Returns:
            Dict[str, Any]: Statistiques du cache
        """
        return {
            'memory_size': len(self.memory_cache),
            'redis_size': len(self.redis_client.keys()),
            'lru_cache_size': len(self.lru_cache.cache_info()),
            'last_cleanup': self.last_cleanup_time,
            'cleanup_interval': self.cleanup_interval,
            'ttl': self.ttl
        }
