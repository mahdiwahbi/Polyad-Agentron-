import logging
from datetime import datetime
from dash import html
import dash_bootstrap_components as dbc
import sys
import os

# Import de Config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
try:
    from config.config import Config
except ImportError:
    # En cas d'échec, créer une classe Config factice
    class Config:
        def __init__(self):
            self.config = {"api": {"chat_endpoint": "http://localhost:5000/api/chat"}}

        def get(self, key, default=None):
            return self.config.get(key, default)

# Créer une classe LearningEngine simplifiée pour éviter les problèmes de dépendances
class SimpleLearningEngine:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('polyad.simple_learning_engine')

    async def generate_response(self, message, context=None):
        """Génère une réponse simulée pour le message"""
        self.logger.info(f"Génération d'une réponse pour: {message[:30]}...")

        # Réponses prédéfinies pour simulation
        responses = {
            "bonjour": "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
            "aide": "Je suis Polyad, votre assistant IA. Je peux vous aider avec la surveillance système, l'automatisation des tâches et répondre à vos questions.",
            "status": "Tous les systèmes fonctionnent normalement. La surveillance est active.",
            "version": "Polyad v1.0 - Système d'agent autonome multifonctionnel",
        }

        # Chercher une correspondance dans les réponses prédéfinies
        for key, response in responses.items():
            if key in message.lower():
                return response

        # Réponse par défaut
        return "Je suis connecté à l'API Polyad. Pour interagir complètement avec le système, assurez-vous que l'API est en cours d'exécution à l'adresse http://localhost:5000."

logger = logging.getLogger('polyad.chat')

class Chat:
    def __init__(self):
        """Initialise le composant de chat"""
        self.config = Config()
        self.learning_engine = SimpleLearningEngine(self.config.config)
        self.message_history = []
        self.max_messages = self.config.get('ui', {}).get('chat', {}).get('max_messages', 100)

    def create_chat_history(self, message: str, response: str) -> html.Div:
        """Crée l'historique des messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Style pour les messages
        user_style = {
            "text-align": "right",
            "background-color": "#375a7f",
            "color": "white",
            "border-radius": "15px 15px 0 15px",
            "padding": "10px 15px",
            "margin": "5px 0",
            "max-width": "80%",
            "display": "inline-block"
        }

        ai_style = {
            "text-align": "left",
            "background-color": "#444",
            "color": "white",
            "border-radius": "15px 15px 15px 0",
            "padding": "10px 15px",
            "margin": "5px 0",
            "max-width": "80%",
            "display": "inline-block"
        }

        # Création des bulles de message
        message_div = html.Div([
            html.Div([
                html.Span(f"Vous ({timestamp})", style={"font-size": "0.8em", "color": "#aaa"}),
                html.Div(message, style=user_style)
            ], style={"text-align": "right", "margin-bottom": "10px"}),
            html.Div([
                html.Span(f"Polyad ({timestamp})", style={"font-size": "0.8em", "color": "#aaa"}),
                html.Div(response, style=ai_style)
            ], style={"text-align": "left", "margin-bottom": "10px"})
        ])

        return message_div

    def create_chat_component(self) -> html.Div:
        """Crée le composant de chat"""
        chat_component = html.Div([
            # Titre
            html.H4("Assistant Polyad", className="mb-4"),

            # Zone d'historique des messages
            html.Div(
                id="chat-history",
                style={
                    "height": "400px",
                    "overflow-y": "auto",
                    "padding": "10px",
                    "background-color": "#222",
                    "border-radius": "5px",
                    "margin-bottom": "15px"
                }
            ),

            # Zone de saisie et bouton d'envoi
            dbc.InputGroup([
                dbc.Input(
                    id="chat-input",
                    placeholder="Entrez votre message...",
                    type="text",
                    debounce=True,
                    style={"background-color": "#333", "color": "white"}
                ),
                dbc.Button(
                    "Envoyer",
                    id="send-button",
                    color="success",
                    className="ms-2"
                )
            ])
        ], className="p-4", style={"background-color": "#303030", "border-radius": "5px"})

        return chat_component

    async def process_message(self, message: str) -> str:
        """Traite un message et retourne une réponse"""
        logger.info(f"Traitement du message: {message[:30]}{'...' if len(message) > 30 else ''}")

        try:
            # Utiliser le moteur d'apprentissage pour générer une réponse
            context = {"message": message, "timestamp": datetime.now().isoformat()}
            response = await self.learning_engine.generate_response(message, context)

            # Limiter l'historique des messages
            if len(self.message_history) >= self.max_messages:
                self.message_history.pop(0)

            # Ajouter le message à l'historique
            self.message_history.append({"user": message, "ai": response, "timestamp": datetime.now().isoformat()})

            return response
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            return f"Désolé, je n'ai pas pu traiter votre demande. Erreur: {str(e)}"
