from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime
from dash import html
from core.learning_engine import LearningEngine
from config.config import Config

logger = logging.getLogger('polyad.chat')

class Chat:
    def __init__(self):
        """Initialise le composant de chat"""
        self.config = Config()
        self.learning_engine = LearningEngine(self.config.data)
        self.message_history = []
        self.max_messages = self.config.data.get('ui', {}).get('chat', {}).get('max_messages', 100)
        
    def create_chat_history(self, message: str, response: str) -> html.Div:
        """Crée l'historique des messages"""
        # Ajouter le message à l'historique
        self.message_history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response
        })
        
        # Limiter la taille de l'historique
        if len(self.message_history) > self.max_messages:
            self.message_history = self.message_history[-self.max_messages:]
            
        # Créer les composants HTML
        messages = []
        for msg in reversed(self.message_history):
            messages.extend([
                html.Div(
                    html.P(msg['message'], className="user-message"),
                    className="message-container user"
                ),
                html.Div(
                    html.P(msg['response'], className="ai-message"),
                    className="message-container ai"
                )
            ])
            
        return html.Div(
            messages,
            className="chat-history",
            style={
                "height": "100%",
                "overflow-y": "auto"
            }
        )
        
    async def process_message(self, message: str) -> str:
        """Traite un message utilisateur"""
        try:
            # Analyser le message et déterminer l'intention
            intent = await self._analyze_intent(message)
            
            # Traiter selon le type d'intention
            if intent['type'] == 'command':
                return await self._handle_command(message)
            elif intent['type'] == 'web_search':
                return await self._handle_web_search(message)
            elif intent['type'] == 'content_generation':
                return await self._handle_content_generation(message)
            else:
                return await self.learning_engine.process_message(message)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            return "Je suis désolé, une erreur est survenue lors du traitement de votre message."
            
    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyse l'intention du message"""
        # Utiliser le moteur d'apprentissage pour l'analyse
        return await self.learning_engine._analyze_intent(message)
        
    async def _handle_command(self, message: str) -> str:
        """Gère les commandes système"""
        # Utiliser l'outil système du moteur d'apprentissage
        return await self.learning_engine._execute_system_command(message)
        
    async def _handle_web_search(self, message: str) -> str:
        """Gère les recherches web"""
        # Utiliser la chaîne de recherche web
        return await self.learning_engine.web_research_chain.run(message)
        
    async def _handle_content_generation(self, message: str) -> str:
        """Gère la génération de contenu"""
        # Utiliser la chaîne de génération de contenu
        return await self.learning_engine.conversation_chain.run(message)
        
    def get_capabilities(self) -> List[str]:
        """Retourne la liste des capacités"""
        return self.learning_engine.get_capabilities()
        
    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état du chat"""
        return {
            'message_count': len(self.message_history),
            'max_messages': self.max_messages,
            'capabilities': self.get_capabilities(),
            'learning_status': self.learning_engine.get_status()
        }
