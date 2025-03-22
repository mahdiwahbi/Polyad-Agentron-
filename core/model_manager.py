from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

from utils.logger import logger
from .ollama_client import OllamaClient

class ModelManager:
    """
    Gestionnaire de modèles Ollama avec focus sur gemma3:12b-it-q4_K_M
    """
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.primary_model = "gemma3:12b-it-q4_K_M"
        
        # Configuration des modèles disponibles
        self.models = {
            'primary': {
                'name': 'gemma3:12b-it-q4_K_M',
                'ram_required': 2 * 1024 * 1024 * 1024,  # Réduit pour compatibilité locale
                'performance_score': 1.0,
                'description': 'Modèle Gemma 3 12B optimisé pour les tâches interactives'
            },
            'fallback': {
                'name': 'gemma3:12b-it-q4_K_M',  # Utilisation du même modèle comme fallback
                'ram_required': 2 * 1024 * 1024 * 1024,  # Réduit pour compatibilité locale
                'performance_score': 1.0,
                'description': 'Modèle Gemma 3 12B optimisé pour les tâches interactives'
            },
            'lightweight': {
                'name': 'gemma3:12b-it-q4_K_M',  # Utilisation du même modèle comme lightweight
                'ram_required': 2 * 1024 * 1024 * 1024,  # Réduit pour compatibilité locale
                'performance_score': 1.0,
                'description': 'Modèle Gemma 3 12B optimisé pour les tâches interactives'
            }
        }
        
        self.current_model = None
        self.model_stats = {}
        self.ollama_client = None
        
    async def initialize(self, system_info: Dict[str, Any]) -> bool:
        """Initialiser le gestionnaire de modèles avec les informations système"""
        try:
            # Initialiser le client Ollama
            self.ollama_client = OllamaClient(host=self.host, model=self.primary_model)
            client_init = await self.ollama_client.initialize()
            
            if not client_init:
                logger.error("Échec d'initialisation du client Ollama")
                return False
            
            # Sélectionner le modèle initial basé sur la RAM disponible
            available_ram = system_info.get('ram_gb', 0) * 1024 * 1024 * 1024
            self.current_model = await self.select_model({'ram_available': available_ram})
            
            # Charger les statistiques existantes
            await self.load_stats()
            
            logger.info(f"Gestionnaire de modèles initialisé avec: {self.current_model['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Échec d'initialisation du gestionnaire de modèles: {e}")
            return False
            
    async def select_model(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Sélectionner le modèle approprié basé sur les ressources disponibles"""
        try:
            available_ram = resources.get('ram_available', 0)
            
            # Essayer par ordre de préférence, de primary à lightweight
            for model_type in ['primary', 'fallback', 'lightweight']:
                model = self.models[model_type]
                if available_ram >= model['ram_required']:
                    # Si c'est un modèle différent, mettre à jour le client Ollama
                    if self.current_model != model:
                        logger.info(f"Passage au modèle: {model['name']}")
                        self.current_model = model
                        self.ollama_client.model = model['name']
                        
                        # Vérifier si le modèle est disponible
                        models = await self.ollama_client.list_models()
                        if model['name'] not in [m['name'] for m in models]:
                            logger.info(f"Téléchargement du modèle {model['name']}...")
                            await self.ollama_client.pull_model()
                    
                    return model
                    
            # Si aucun modèle ne correspond, utiliser le plus léger
            logger.warning("Ressources insuffisantes, utilisation du modèle le plus léger")
            self.current_model = self.models['lightweight']
            self.ollama_client.model = self.models['lightweight']['name']
            return self.models['lightweight']
            
        except Exception as e:
            logger.error(f"Échec de sélection du modèle: {e}")
            if self.current_model:
                return self.current_model
            return self.models['lightweight']
            
    def update_stats(self, model_name: str, metrics: Dict[str, Any]):
        """Update model performance statistics"""
        try:
            if model_name not in self.model_stats:
                self.model_stats[model_name] = {
                    'total_runs': 0,
                    'success_runs': 0,
                    'total_tokens': 0,
                    'total_time': 0,
                    'errors': 0,
                    'history': []
                }
                
            stats = self.model_stats[model_name]
            stats['total_runs'] += 1
            
            if metrics.get('success', False):
                stats['success_runs'] += 1
                
            stats['total_tokens'] += metrics.get('tokens', 0)
            stats['total_time'] += metrics.get('time', 0)
            
            if 'error' in metrics:
                stats['errors'] += 1
                
            # Keep last 100 runs in history
            stats['history'].append({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            })
            if len(stats['history']) > 100:
                stats['history'] = stats['history'][-100:]
                
        except Exception as e:
            logger.error(f"Failed to update model stats: {e}")
            
    def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics for a model"""
        try:
            if model_name is None and self.current_model:
                model_name = self.current_model['name']
                
            if model_name in self.model_stats:
                stats = self.model_stats[model_name]
                return {
                    'success_rate': stats['success_runs'] / stats['total_runs'] if stats['total_runs'] > 0 else 0,
                    'avg_tokens_per_run': stats['total_tokens'] / stats['total_runs'] if stats['total_runs'] > 0 else 0,
                    'avg_time_per_run': stats['total_time'] / stats['total_runs'] if stats['total_runs'] > 0 else 0,
                    'error_rate': stats['errors'] / stats['total_runs'] if stats['total_runs'] > 0 else 0,
                    'total_runs': stats['total_runs']
                }
                
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return {}
            
    async def save_stats(self, path: str = 'data/model_stats.json'):
        """Save model statistics to file"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(self.model_stats, f)
                
        except Exception as e:
            logger.error(f"Failed to save model stats: {e}")
            
    async def load_stats(self, path: str = 'data/model_stats.json'):
        """Load model statistics from file"""
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.model_stats = json.load(f)
                    
        except Exception as e:
            logger.error(f"Failed to load model stats: {e}")
            
    async def generate_response(self, prompt: str, system: Optional[str] = None, 
                        temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Générer une réponse avec le modèle actuel"""
        try:
            start_time = datetime.now()
            response = await self.ollama_client.generate(prompt, system, temperature, max_tokens)
            
            # Calculer la durée
            duration = (datetime.now() - start_time).total_seconds()
            
            # Mettre à jour les statistiques
            metrics = {
                'success': 'error' not in response,
                'tokens': response.get('usage', {}).get('total_tokens', 0),
                'time': duration
            }
            
            if 'error' in response:
                metrics['error'] = response['error']
                
            self.update_stats(self.current_model['name'], metrics)
            
            return response
            
        except Exception as e:
            logger.error(f"Échec de génération: {e}")
            return {'error': str(e)}
            
    async def chat(self, messages: list, system: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Interagir avec le modèle en mode chat"""
        try:
            start_time = datetime.now()
            response = await self.ollama_client.chat(messages, system, temperature, max_tokens)
            
            # Calculer la durée
            duration = (datetime.now() - start_time).total_seconds()
            
            # Mettre à jour les statistiques
            metrics = {
                'success': 'error' not in response,
                'tokens': response.get('usage', {}).get('total_tokens', 0),
                'time': duration
            }
            
            if 'error' in response:
                metrics['error'] = response['error']
                
            self.update_stats(self.current_model['name'], metrics)
            
            return response
            
        except Exception as e:
            logger.error(f"Échec de chat: {e}")
            return {'error': str(e)}
            
    async def process_image(self, image_path: str, prompt: str, system: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Traiter une image avec le modèle actuel"""
        try:
            start_time = datetime.now()
            response = await self.ollama_client.process_image(image_path, prompt, system, temperature, max_tokens)
            
            # Calculer la durée
            duration = (datetime.now() - start_time).total_seconds()
            
            # Mettre à jour les statistiques
            metrics = {
                'success': 'error' not in response,
                'tokens': response.get('usage', {}).get('total_tokens', 0),
                'time': duration,
                'type': 'image'
            }
            
            if 'error' in response:
                metrics['error'] = response['error']
                
            self.update_stats(self.current_model['name'], metrics)
            
            return response
            
        except Exception as e:
            logger.error(f"Échec de traitement d'image: {e}")
            return {'error': str(e)}
            
    async def get_embeddings(self, text: str) -> Dict[str, Any]:
        """Obtenir les embeddings pour un texte"""
        try:
            response = await self.ollama_client.get_embeddings(text)
            return response
        except Exception as e:
            logger.error(f"Échec d'obtention d'embeddings: {e}")
            return {'error': str(e)}
            
    async def cleanup(self):
        """Nettoyer les ressources du gestionnaire de modèles"""
        if self.ollama_client:
            await self.ollama_client.close()
            
    @property
    def available_models(self) -> Dict[str, Dict[str, Any]]:
        """Obtenir la liste des modèles disponibles"""
        return self.models
