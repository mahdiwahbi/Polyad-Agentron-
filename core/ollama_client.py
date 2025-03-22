"""
Client pour interagir avec Ollama
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, List, Optional
import base64

from utils.logger import logger

class OllamaClient:
    """
    Client asynchrone pour interagir avec l'API Ollama
    """
    def __init__(self, host: str = "http://localhost:11434", model: str = "gemma3:12b-it-q4_K_M"):
        self.host = host
        self.model = model
        self.api_generate = f"{host}/api/generate"
        self.api_embeddings = f"{host}/api/embeddings"
        self.api_chat = f"{host}/api/chat"
        self.api_models = f"{host}/api/tags"
        self.session = None
        
    async def initialize(self) -> bool:
        """Initialiser la session HTTP et vérifier la disponibilité du modèle"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Vérifier que le modèle est disponible
            models = await self.list_models()
            
            if self.model not in [model['name'] for model in models]:
                logger.warning(f"Le modèle {self.model} n'est pas disponible. Tentative de téléchargement...")
                await self.pull_model()
                
            return True
        except Exception as e:
            logger.error(f"Erreur d'initialisation du client Ollama: {e}")
            return False
            
    async def close(self):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()
            
    async def list_models(self) -> List[Dict[str, Any]]:
        """Lister les modèles disponibles"""
        try:
            async with self.session.get(self.api_models) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['models']
                else:
                    error = await response.text()
                    logger.error(f"Erreur lors de la récupération des modèles: {error}")
                    return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []
            
    async def pull_model(self) -> bool:
        """Télécharger le modèle s'il n'est pas disponible"""
        try:
            url = f"{self.host}/api/pull"
            async with self.session.post(url, json={"name": self.model}) as response:
                if response.status == 200:
                    logger.info(f"Modèle {self.model} téléchargé avec succès")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Erreur lors du téléchargement du modèle: {error}")
                    return False
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du modèle: {e}")
            return False
            
    async def generate(self, prompt: str, system: Optional[str] = None, 
                      temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Générer une réponse à partir d'un prompt"""
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if system:
                data["system"] = system
                
            async with self.session.post(self.api_generate, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "text": result.get("response", ""),
                        "model": self.model,
                        "usage": {
                            "prompt_tokens": result.get("prompt_eval_count", 0),
                            "completion_tokens": result.get("eval_count", 0),
                            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                        }
                    }
                else:
                    error = await response.text()
                    logger.error(f"Erreur de génération: {error}")
                    return {"error": error}
        except Exception as e:
            logger.error(f"Erreur de génération: {e}")
            return {"error": str(e)}
            
    async def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None,
                  temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Converser avec le modèle"""
        try:
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if system:
                data["system"] = system
                
            async with self.session.post(self.api_chat, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "message": result.get("message", {}),
                        "model": self.model,
                        "usage": {
                            "input_tokens": result.get("prompt_eval_count", 0),
                            "output_tokens": result.get("eval_count", 0),
                            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                        }
                    }
                else:
                    error = await response.text()
                    logger.error(f"Erreur de chat: {error}")
                    return {"error": error}
        except Exception as e:
            logger.error(f"Erreur de chat: {e}")
            return {"error": str(e)}
            
    async def get_embeddings(self, text: str) -> Dict[str, Any]:
        """Obtenir les embeddings d'un texte"""
        try:
            data = {
                "model": self.model,
                "prompt": text
            }
            
            async with self.session.post(self.api_embeddings, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "embedding": result.get("embedding", []),
                        "model": self.model
                    }
                else:
                    error = await response.text()
                    logger.error(f"Erreur d'embeddings: {error}")
                    return {"error": error}
        except Exception as e:
            logger.error(f"Erreur d'embeddings: {e}")
            return {"error": str(e)}
            
    async def process_image(self, image_path: str, prompt: str, system: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """Traiter une image avec un modèle multimodal"""
        try:
            # Encoder l'image en base64
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")
                
            # Format pour modèles de vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": image_base64}
                    ]
                }
            ]
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if system:
                data["system"] = system
                
            async with self.session.post(self.api_chat, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "message": result.get("message", {}),
                        "model": self.model,
                        "usage": {
                            "input_tokens": result.get("prompt_eval_count", 0),
                            "output_tokens": result.get("eval_count", 0),
                            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                        }
                    }
                else:
                    error = await response.text()
                    logger.error(f"Erreur de traitement d'image: {error}")
                    return {"error": error}
        except Exception as e:
            logger.error(f"Erreur de traitement d'image: {e}")
            return {"error": str(e)}
