from typing import Dict, Any, Optional
import logging
from polyad.utils.config import Config
from polyad.services.cache import CacheManager
from polyad.services.monitoring import MonitoringService
from polyad.services.model import ModelManager
import asyncio

class PolyadAgent:
    def __init__(self, config: Config):
        """Initialise l'agent avec configuration sécurisée"""
        self.config = config
        self.logger = logging.getLogger('polyad.agent')
        self.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
        
        # Initialiser les services avec validation
        self._validate_config()
        self.cache = CacheManager(config)
        self.monitoring = MonitoringService(config)
        self.model_manager = ModelManager(config)
        
        # États de l'agent
        self.is_running = False
        self.tasks: Dict[str, asyncio.Task] = {}

    def _validate_config(self) -> None:
        """Valide la configuration"""
        required_fields = ['cache_size', 'batch_size', 'parallel_workers', 'max_queue_size']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Configuration manquante: {field}")
            if not isinstance(self.config[field], (int, float)) or self.config[field] <= 0:
                raise ValueError(f"Valeur invalide pour {field}")

    async def initialize(self) -> bool:
        """Initialise l'agent avec gestion des erreurs"""
        try:
            self.logger.info("Initialisation de l'agent...")
            
            # Initialiser les services
            await self.cache.initialize()
            await self.monitoring.initialize()
            await self.model_manager.initialize()
            
            self.logger.info("Agent initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Échec de l'initialisation: {e}")
            return False

    async def start(self) -> None:
        """Démarre l'agent avec gestion des erreurs"""
        if self.is_running:
            self.logger.warning("L'agent est déjà en cours d'exécution")
            return
            
        try:
            self.logger.info("Démarrage de l'agent...")
            self.is_running = True
            
            # Démarrer la surveillance
            await self.monitoring.start()
            
            # Démarrer le cache
            await self.cache.start()
            
            # Démarrer le gestionnaire de modèles
            await self.model_manager.start()
            
            self.logger.info("Agent démarré avec succès")
            
        except Exception as e:
            self.logger.error(f"Échec du démarrage: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Arrête l'agent avec nettoyage"""
        if not self.is_running:
            return
            
        try:
            self.logger.info("Arrêt de l'agent...")
            self.is_running = False
            
            # Arrêter les services dans l'ordre inverse
            await self.model_manager.stop()
            await self.cache.stop()
            await self.monitoring.stop()
            
            # Nettoyer les tâches
            for task in self.tasks.values():
                task.cancel()
            
            self.logger.info("Agent arrêté avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")
            raise

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une requête avec validation"""
        try:
            self._validate_request(request)
            return await self._process_request_internal(request)
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Valide une requête"""
        required_fields = ['type', 'action']
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Champ requis manquant: {field}")
            if not isinstance(request[field], str):
                raise ValueError(f"{field} doit être une chaîne")

    async def _process_request_internal(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une requête"""
        # Implémentation spécifique au type de requête
        pass
