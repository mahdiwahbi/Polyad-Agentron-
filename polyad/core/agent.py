import asyncio
import logging
from typing import Dict, Any
import os

from ..utils.config import ConfigManager
from polyad.utils.logging import setup_logging
from polyad.services.cache import CacheManager
from polyad.services.monitoring import MonitoringService
from polyad.services.model import ModelManager

class PolyadAgent:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger('polyad.agent')
        
        # Initialiser les services
        self.cache_manager = CacheManager(config)
        self.model_manager = ModelManager(config)
        self.monitoring_service = MonitoringService(config)
        
        # États de l'agent
        self.is_running = False
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Démarrer l'agent"""
        self.logger.info("Démarrage de l'agent Polyad...")
        
        try:
            # Démarrer les services
            self.logger.info("Démarrage des services...")
            await self.monitoring_service.start()
            await self.cache_manager.start()
            await self.model_manager.start()

            self.logger.info("Agent Polyad démarré avec succès")
            
            # Maintenir l'agent en cours d'exécution
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage : {str(e)}")
            raise

    async def stop(self):
        """Arrêter l'agent proprement"""
        self.logger.info("Arrêt de l'agent Polyad...")
        self.is_running = False
        
        try:
            self.logger.info("Arrêt des services en cours...")
            await self.model_manager.stop()
            await self.cache_manager.stop()
            await self.monitoring_service.stop()

            self.logger.info("Agent Polyad arrêté avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt : {str(e)}")
            raise

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter une requête"""
        try:
            # Vérifier le cache
            cached_response = await self.cache_manager.get(request)
            if cached_response:
                return cached_response
            
            # Traiter la requête avec le modèle
            response = await self.model_manager.process(request)
            
            # Mettre en cache la réponse
            await self.cache_manager.set(request, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de la requête : {str(e)}")
            raise
