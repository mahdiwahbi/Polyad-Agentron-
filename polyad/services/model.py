import asyncio
import logging
from typing import Dict, Any, Optional
import os
from ollama import Client
from ..utils.config import ConfigManager

class ModelManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger('polyad.model')
        
        # Configuration Ollama
        self.ollama_config = {
            'host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
            'model': os.getenv('OLLAMA_MODEL', 'gemma3:12b-it-q4_K_M')
        }
        
        # Initialiser le client Ollama
        self.client: Optional[Client] = None
        
        # État du gestionnaire
        self.is_running = False
        self.model_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialiser le gestionnaire de modèle"""
        self.logger.info("Initialisation du gestionnaire de modèle...")
        
        try:
            # Initialiser le client Ollama
            self.client = Client(self.ollama_config['host'])
            
            # Vérifier si le modèle est disponible
            if not await self.is_model_available():
                self.logger.info(f"Chargement du modèle {self.ollama_config['model']}...")
                await self.client.pull(self.ollama_config['model'])
            
            self.logger.info("Gestionnaire de modèle initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation du modèle : {str(e)}")
            raise

    async def start(self):
        """Démarrer le gestionnaire de modèle"""
        self.is_running = True
        self.model_task = asyncio.create_task(self.monitor_model())

    async def stop(self):
        """Arrêter le gestionnaire de modèle"""
        self.is_running = False
        if self.model_task:
            self.model_task.cancel()
            try:
                await self.model_task
            except asyncio.CancelledError:
                pass

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter une requête avec le modèle"""
        try:
            # Préparer la requête
            prompt = request.get('prompt', '')
            system = request.get('system', None)
            temperature = request.get('temperature', self.config.model['temperature'])
            max_tokens = request.get('max_tokens', self.config.model['max_tokens'])
            
            # Générer une réponse
            response = await self.client.generate(
                model=self.ollama_config['model'],
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                'success': True,
                'response': response,
                'model': self.ollama_config['model']
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de la requête : {str(e)}")
            raise

    async def is_model_available(self) -> bool:
        """Vérifier si le modèle est disponible"""
        try:
            models = await self.client.models()
            return any(m['name'] == self.ollama_config['model'] for m in models)
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du modèle : {str(e)}")
            return False

    async def monitor_model(self):
        """Surveiller l'état du modèle"""
        while self.is_running:
            try:
                # Ici, vous pouvez ajouter la surveillance spécifique du modèle
                await asyncio.sleep(60)  # Vérifier toutes les minutes
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance du modèle : {str(e)}")
                await asyncio.sleep(5)  # Attente avant de réessayer
