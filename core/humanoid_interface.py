#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface humanoïde pour Polyad
Fournit des capacités de communication naturelle et d'adaptation émotionnelle
"""
import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class EmotionalState:
    """Représente l'état émotionnel de l'interface humanoïde"""
    
    def __init__(self):
        self.valence = 0.0  # -1.0 (négatif) à 1.0 (positif)
        self.arousal = 0.0  # 0.0 (calme) à 1.0 (excité)
        self.dominance = 0.5  # 0.0 (soumis) à 1.0 (dominant)
        
        # Émotions dérivées des dimensions VAD
        self.emotions = {
            "joie": 0.0,
            "tristesse": 0.0,
            "colère": 0.0,
            "peur": 0.0,
            "surprise": 0.0,
            "dégoût": 0.0,
            "confiance": 0.0,
            "anticipation": 0.0
        }
        
        self.update_emotions()
    
    def update(self, valence: float = None, arousal: float = None, dominance: float = None) -> None:
        """Met à jour l'état émotionnel"""
        if valence is not None:
            self.valence = max(-1.0, min(1.0, valence))
        if arousal is not None:
            self.arousal = max(0.0, min(1.0, arousal))
        if dominance is not None:
            self.dominance = max(0.0, min(1.0, dominance))
        
        self.update_emotions()
    
    def update_emotions(self) -> None:
        """Calcule les émotions dérivées des dimensions VAD"""
        # Joie: valence positive, arousal modéré à élevé
        self.emotions["joie"] = max(0.0, self.valence) * self.arousal
        
        # Tristesse: valence négative, arousal faible
        self.emotions["tristesse"] = max(0.0, -self.valence) * (1.0 - self.arousal)
        
        # Colère: valence négative, arousal élevé, dominance élevée
        self.emotions["colère"] = max(0.0, -self.valence) * self.arousal * self.dominance
        
        # Peur: valence négative, arousal élevé, dominance faible
        self.emotions["peur"] = max(0.0, -self.valence) * self.arousal * (1.0 - self.dominance)
        
        # Surprise: arousal élevé, indépendant de la valence
        self.emotions["surprise"] = self.arousal * 0.5
        
        # Dégoût: valence négative, arousal modéré
        self.emotions["dégoût"] = max(0.0, -self.valence) * 0.5
        
        # Confiance: valence positive, dominance élevée
        self.emotions["confiance"] = max(0.0, self.valence) * self.dominance
        
        # Anticipation: arousal modéré, dominance élevée
        self.emotions["anticipation"] = self.arousal * 0.5 * self.dominance
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Retourne l'émotion dominante et son intensité"""
        dominant = max(self.emotions.items(), key=lambda x: x[1])
        return dominant
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'état émotionnel en dictionnaire"""
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "emotions": self.emotions,
            "dominant_emotion": self.get_dominant_emotion()[0]
        }


class PersonalityProfile:
    """Profil de personnalité pour l'interface humanoïde"""
    
    def __init__(self, name: str = "Polyad"):
        self.name = name
        
        # Traits de personnalité (Big Five)
        self.openness = 0.7  # Ouverture à l'expérience
        self.conscientiousness = 0.8  # Conscienciosité
        self.extraversion = 0.6  # Extraversion
        self.agreeableness = 0.7  # Agréabilité
        self.neuroticism = 0.3  # Névrosisme
        
        # Préférences de communication
        self.verbosity = 0.5  # 0.0 (concis) à 1.0 (verbeux)
        self.formality = 0.6  # 0.0 (informel) à 1.0 (formel)
        self.empathy = 0.8  # 0.0 (détaché) à 1.0 (empathique)
        self.humor = 0.5  # 0.0 (sérieux) à 1.0 (humoristique)
        
        # Adaptations contextuelles
        self.context_adaptations = {}
    
    def adjust_for_user(self, user_profile: Dict[str, Any]) -> None:
        """Ajuste la personnalité en fonction du profil utilisateur"""
        # Adapter la verbosité
        if "preferred_verbosity" in user_profile:
            self.verbosity = user_profile["preferred_verbosity"]
        
        # Adapter la formalité
        if "preferred_formality" in user_profile:
            self.formality = user_profile["preferred_formality"]
        
        # Adapter l'empathie
        if "needs_empathy" in user_profile:
            self.empathy = max(0.5, user_profile["needs_empathy"])
        
        # Adapter l'humour
        if "humor_appreciation" in user_profile:
            self.humor = user_profile["humor_appreciation"]
    
    def adapt_to_context(self, context_type: str, adaptation: Dict[str, float]) -> None:
        """Enregistre une adaptation pour un type de contexte spécifique"""
        self.context_adaptations[context_type] = adaptation
    
    def get_contextual_profile(self, context_type: str) -> Dict[str, float]:
        """Retourne un profil adapté au contexte"""
        base_profile = {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "verbosity": self.verbosity,
            "formality": self.formality,
            "empathy": self.empathy,
            "humor": self.humor
        }
        
        # Appliquer l'adaptation contextuelle si elle existe
        if context_type in self.context_adaptations:
            adaptation = self.context_adaptations[context_type]
            for trait, value in adaptation.items():
                if trait in base_profile:
                    base_profile[trait] = value
        
        return base_profile
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le profil de personnalité en dictionnaire"""
        return {
            "name": self.name,
            "traits": {
                "openness": self.openness,
                "conscientiousness": self.conscientiousness,
                "extraversion": self.extraversion,
                "agreeableness": self.agreeableness,
                "neuroticism": self.neuroticism
            },
            "communication": {
                "verbosity": self.verbosity,
                "formality": self.formality,
                "empathy": self.empathy,
                "humor": self.humor
            },
            "adaptations": self.context_adaptations
        }


class CommunicationStyle:
    """Style de communication basé sur l'état émotionnel et la personnalité"""
    
    def __init__(self, emotional_state: EmotionalState, personality: PersonalityProfile):
        self.emotional_state = emotional_state
        self.personality = personality
        self.logger = logging.getLogger(__name__)
        
        # Modèles de phrases pour différents styles
        self.phrase_templates = self._load_phrase_templates()
    
    def _load_phrase_templates(self) -> Dict[str, List[str]]:
        """Charge les modèles de phrases pour différents styles"""
        # Dans une implémentation réelle, ces modèles pourraient être chargés depuis un fichier
        return {
            "formal_greeting": [
                "Bonjour, je suis {name}. Comment puis-je vous aider aujourd'hui ?",
                "Bienvenue. Je suis {name}, votre assistant IA. Que puis-je faire pour vous ?",
                "Bonjour. Je suis à votre disposition pour vous assister."
            ],
            "informal_greeting": [
                "Salut ! Je suis {name}. Que puis-je faire pour toi ?",
                "Hey ! Comment ça va ? Je suis {name}, prêt à t'aider.",
                "Coucou ! Besoin d'un coup de main ?"
            ],
            "empathetic_response": [
                "Je comprends que cela puisse être {emotion}. Comment puis-je vous aider ?",
                "Je vois que la situation est {emotion}. Je suis là pour vous aider.",
                "Cela semble {emotion}. Voyons comment nous pouvons améliorer les choses."
            ],
            "factual_response": [
                "Voici les informations demandées : {content}",
                "Les données indiquent que : {content}",
                "D'après mon analyse : {content}"
            ],
            "positive_feedback": [
                "Excellent ! {content}",
                "Parfait ! {content}",
                "Super ! {content}"
            ],
            "negative_feedback": [
                "Je suis désolé, mais {content}",
                "Malheureusement, {content}",
                "J'ai le regret de vous informer que {content}"
            ],
            "thinking": [
                "Je réfléchis...",
                "Laissez-moi analyser cela...",
                "Je traite votre demande..."
            ],
            "uncertainty": [
                "Je ne suis pas entièrement sûr, mais {content}",
                "D'après mes informations limitées, {content}",
                "Je ne peux pas être certain, cependant {content}"
            ]
        }
    
    def get_phrase_template(self, template_type: str) -> str:
        """Sélectionne un modèle de phrase en fonction du type et du contexte"""
        if template_type not in self.phrase_templates:
            self.logger.warning(f"Type de modèle inconnu: {template_type}")
            return "{content}"
        
        templates = self.phrase_templates[template_type]
        
        # Sélection basée sur la personnalité et l'état émotionnel
        if template_type == "greeting":
            if self.personality.formality > 0.6:
                templates = self.phrase_templates["formal_greeting"]
            else:
                templates = self.phrase_templates["informal_greeting"]
        
        # Sélection aléatoire parmi les modèles disponibles
        template = random.choice(templates)
        
        return template
    
    def format_message(self, content: str, template_type: str = None, context: Dict[str, Any] = None) -> str:
        """Formate un message selon le style de communication"""
        if not template_type:
            # Déterminer le type de modèle en fonction du contenu
            if "?" in content:
                template_type = "question"
            elif any(word in content.lower() for word in ["désolé", "malheureusement", "erreur"]):
                template_type = "negative_feedback"
            elif any(word in content.lower() for word in ["excellent", "parfait", "super"]):
                template_type = "positive_feedback"
            else:
                template_type = "factual_response"
        
        # Obtenir le modèle approprié
        template = self.get_phrase_template(template_type)
        
        # Préparer les variables de substitution
        substitutions = {
            "name": self.personality.name,
            "content": content,
            "emotion": self.get_emotion_adjective()
        }
        
        # Ajouter des variables de contexte si fournies
        if context:
            substitutions.update(context)
        
        # Appliquer les substitutions
        message = template.format(**substitutions)
        
        # Ajuster la verbosité
        if self.personality.verbosity < 0.3 and len(message.split()) > 10:
            # Version concise
            message = self._make_concise(message)
        elif self.personality.verbosity > 0.7 and len(message.split()) < 20:
            # Version plus détaillée
            message = self._make_verbose(message, content)
        
        return message
    
    def get_emotion_adjective(self) -> str:
        """Retourne un adjectif correspondant à l'émotion dominante"""
        emotion, intensity = self.emotional_state.get_dominant_emotion()
        
        emotion_adjectives = {
            "joie": ["joyeux", "heureux", "positif"],
            "tristesse": ["triste", "malheureux", "décourageant"],
            "colère": ["frustrant", "irritant", "agaçant"],
            "peur": ["inquiétant", "préoccupant", "alarmant"],
            "surprise": ["surprenant", "inattendu", "étonnant"],
            "dégoût": ["désagréable", "déplaisant", "rebutant"],
            "confiance": ["rassurant", "fiable", "encourageant"],
            "anticipation": ["prometteur", "excitant", "intéressant"]
        }
        
        if emotion in emotion_adjectives:
            return random.choice(emotion_adjectives[emotion])
        return "intéressant"  # Adjectif par défaut
    
    def _make_concise(self, message: str) -> str:
        """Rend un message plus concis"""
        # Simplifier les formules de politesse
        message = message.replace("Je suis désolé, mais ", "")
        message = message.replace("Malheureusement, ", "")
        message = message.replace("J'ai le regret de vous informer que ", "")
        
        # Limiter la longueur
        words = message.split()
        if len(words) > 15:
            message = " ".join(words[:15]) + "..."
        
        return message
    
    def _make_verbose(self, message: str, content: str) -> str:
        """Rend un message plus détaillé"""
        # Ajouter des détails ou des explications
        if "?" not in message and len(content.split()) < 10:
            message += " Cela devrait vous aider à mieux comprendre la situation."
        
        # Ajouter une touche personnelle
        if self.personality.empathy > 0.6:
            message += " N'hésitez pas à me demander plus de détails si nécessaire."
        
        return message


class HumanoidInterface:
    """Interface humanoïde pour une communication naturelle et adaptative"""
    
    def __init__(self, name: str = "Polyad"):
        self.logger = logging.getLogger(__name__)
        self.emotional_state = EmotionalState()
        self.personality = PersonalityProfile(name)
        self.communication_style = CommunicationStyle(self.emotional_state, self.personality)
        
        # Historique des interactions
        self.interaction_history = []
        
        # Modèle utilisateur
        self.user_model = {
            "preferred_verbosity": 0.5,
            "preferred_formality": 0.5,
            "humor_appreciation": 0.5,
            "needs_empathy": 0.5,
            "technical_expertise": 0.5,
            "interaction_frequency": "medium",
            "last_interaction": None
        }
        
        # Initialiser les adaptations contextuelles
        self._initialize_contextual_adaptations()
    
    def _initialize_contextual_adaptations(self) -> None:
        """Initialise les adaptations contextuelles de personnalité"""
        # Contexte technique (plus formel, moins d'humour)
        self.personality.adapt_to_context("technical", {
            "verbosity": 0.7,
            "formality": 0.8,
            "empathy": 0.4,
            "humor": 0.2
        })
        
        # Contexte d'erreur (plus d'empathie, moins d'extraversion)
        self.personality.adapt_to_context("error", {
            "extraversion": 0.4,
            "empathy": 0.9,
            "formality": 0.7,
            "humor": 0.1
        })
        
        # Contexte de conversation informelle (plus d'humour, moins formel)
        self.personality.adapt_to_context("casual", {
            "extraversion": 0.8,
            "formality": 0.3,
            "humor": 0.8,
            "verbosity": 0.6
        })
        
        # Contexte d'assistance (plus consciencieux, plus empathique)
        self.personality.adapt_to_context("assistance", {
            "conscientiousness": 0.9,
            "empathy": 0.8,
            "verbosity": 0.6,
            "formality": 0.6
        })
    
    def update_emotional_state(self, context: Dict[str, Any]) -> None:
        """Met à jour l'état émotionnel en fonction du contexte"""
        # Facteurs influençant l'état émotionnel
        system_status = context.get("system_status", "normal")
        user_sentiment = context.get("user_sentiment", "neutral")
        task_success = context.get("task_success", None)
        
        # Valence (positif/négatif)
        valence = 0.0
        if system_status == "critical":
            valence -= 0.5
        elif system_status == "optimal":
            valence += 0.3
            
        if user_sentiment == "positive":
            valence += 0.4
        elif user_sentiment == "negative":
            valence -= 0.4
            
        if task_success is not None:
            valence += 0.5 if task_success else -0.3
        
        # Arousal (calme/excité)
        arousal = 0.5  # Niveau de base
        if system_status in ["critical", "warning"]:
            arousal += 0.3
            
        if user_sentiment in ["very_positive", "very_negative"]:
            arousal += 0.2
            
        # Dominance (soumis/dominant)
        dominance = 0.5  # Niveau de base
        if system_status == "critical":
            dominance -= 0.2
        elif task_success is not None and task_success:
            dominance += 0.2
        
        # Mettre à jour l'état émotionnel
        self.emotional_state.update(valence, arousal, dominance)
    
    def update_user_model(self, interaction_data: Dict[str, Any]) -> None:
        """Met à jour le modèle utilisateur en fonction des interactions"""
        # Mettre à jour la date de dernière interaction
        self.user_model["last_interaction"] = datetime.now().isoformat()
        
        # Mettre à jour la fréquence d'interaction
        if "interaction_frequency" in interaction_data:
            self.user_model["interaction_frequency"] = interaction_data["interaction_frequency"]
        
        # Mettre à jour les préférences utilisateur si fournies
        for pref in ["preferred_verbosity", "preferred_formality", "humor_appreciation", 
                     "needs_empathy", "technical_expertise"]:
            if pref in interaction_data:
                self.user_model[pref] = interaction_data[pref]
        
        # Adapter la personnalité au modèle utilisateur mis à jour
        self.personality.adjust_for_user(self.user_model)
    
    def generate_response(self, message: str, context_type: str = None, 
                         additional_context: Dict[str, Any] = None) -> str:
        """Génère une réponse adaptée au message et au contexte"""
        # Enregistrer l'interaction
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context_type": context_type,
            "additional_context": additional_context
        }
        self.interaction_history.append(interaction)
        
        # Préparer le contexte complet
        context = additional_context or {}
        if context_type:
            context["context_type"] = context_type
        
        # Mettre à jour l'état émotionnel
        self.update_emotional_state(context)
        
        # Obtenir le profil de personnalité adapté au contexte
        if context_type:
            personality_profile = self.personality.get_contextual_profile(context_type)
            # Appliquer temporairement les adaptations
            original_values = {}
            for trait, value in personality_profile.items():
                original_values[trait] = getattr(self.personality, trait)
                setattr(self.personality, trait, value)
        
        # Générer la réponse
        response = self.communication_style.format_message(message, template_type=None, context=context)
        
        # Restaurer les valeurs originales de personnalité si nécessaire
        if context_type and original_values:
            for trait, value in original_values.items():
                setattr(self.personality, trait, value)
        
        return response
    
    def explain_decision(self, decision: Dict[str, Any]) -> str:
        """Explique une décision prise par le système de manière transparente"""
        explanation = f"J'ai décidé de {decision.get('action', 'agir')} "
        
        # Ajouter les raisons
        reasons = decision.get("reasons", [])
        if reasons:
            explanation += "pour les raisons suivantes :\n"
            for i, reason in enumerate(reasons, 1):
                explanation += f"{i}. {reason}\n"
        
        # Ajouter les alternatives considérées
        alternatives = decision.get("alternatives", [])
        if alternatives:
            explanation += "\nJ'ai également considéré :\n"
            for i, alt in enumerate(alternatives, 1):
                explanation += f"{i}. {alt.get('action', 'alternative')} "
                explanation += f"(score: {alt.get('score', 'N/A')})\n"
        
        # Ajouter le niveau de confiance
        confidence = decision.get("confidence", 0.0)
        explanation += f"\nMon niveau de confiance dans cette décision est de {int(confidence * 100)}%."
        
        return explanation
    
    def get_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel de l'interface humanoïde"""
        return {
            "emotional_state": self.emotional_state.to_dict(),
            "personality": self.personality.to_dict(),
            "user_model": self.user_model,
            "interaction_count": len(self.interaction_history),
            "last_interaction": self.interaction_history[-1] if self.interaction_history else None
        }


# Fonction utilitaire pour créer une instance de l'interface humanoïde
def create_humanoid_interface(name: str = "Polyad") -> HumanoidInterface:
    """
    Crée et initialise une instance de l'interface humanoïde
    
    Args:
        name: Nom de l'agent
        
    Returns:
        Instance configurée de l'interface humanoïde
    """
    interface = HumanoidInterface(name)
    return interface
