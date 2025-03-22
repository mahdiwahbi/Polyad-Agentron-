import asyncio
import logging
from typing import Dict, Any, Optional
import os
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from cachetools import LRUCache
import json

class CacheManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.cache')
        
        # Configuration Redis
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD', None)
        }
        
        # Initialiser les caches
        self.redis: Optional[AsyncRedis] = None
        self.local_cache = LRUCache(maxsize=config.get('cache', {}).get('size', 10000))

    async def initialize(self):
        """Initialiser le cache"""
        self.logger.info("Initialisation du cache...")
        
        try:
            # Initialiser Redis
            self.redis = AsyncRedis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                db=self.redis_config['db'],
                password=self.redis_config['password']
            )
            
            # Tester la connexion
            await self.redis.ping()
            self.logger.info("Cache Redis initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation du cache : {str(e)}")
            raise

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtenir une valeur du cache"""
        # Vérifier le cache local d'abord
        if key in self.local_cache:
            return self.local_cache[key]

        # Vérifier Redis
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    result = json.loads(value)
                    self.local_cache[key] = result
                    return result
            except Exception as e:
                self.logger.error(f"Erreur lors de la lecture du cache Redis : {str(e)}")

        return None

    async def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """Mettre une valeur dans le cache"""
        try:
            # Mettre dans le cache local
            self.local_cache[key] = value
            
            # Mettre dans Redis
            if self.redis:
                try:
                    await self.redis.set(key, json.dumps(value), ex=ttl)
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'écriture dans Redis : {str(e)}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise en cache : {str(e)}")

    async def delete(self, key: str) -> None:
        """Supprimer une valeur du cache"""
        try:
            # Supprimer du cache local
            if key in self.local_cache:
                del self.local_cache[key]
            
            # Supprimer de Redis
            if self.redis:
                try:
                    await self.redis.delete(key)
                except Exception as e:
                    self.logger.error(f"Erreur lors de la suppression dans Redis : {str(e)}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du cache : {str(e)}")

    async def cleanup(self) -> None:
        """Nettoyer le cache"""
        try:
            # Nettoyer le cache local
            self.local_cache.clear()
            
            # Nettoyer Redis
            if self.redis:
                try:
                    await self.redis.flushdb()
                except Exception as e:
                    self.logger.error(f"Erreur lors du nettoyage de Redis : {str(e)}")
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage du cache : {str(e)}")

    async def start(self) -> None:
        """Démarrer le cache"""
        await self.initialize()
        
    async def stop(self) -> None:
        """Arrêter le cache"""
        try:
            await self.cleanup()
            if self.redis:
                await self.redis.close()
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt du cache : {str(e)}")
