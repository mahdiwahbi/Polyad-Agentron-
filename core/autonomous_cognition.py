#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de Cognition Autonome pour Polyad
Ce module fournit des capacités cognitives avancées à Polyad, lui permettant
d'analyser, d'apprendre et de prendre des décisions de manière autonome.
"""
import os
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class PerceptionModule:
    """Module de perception qui observe et interprète l'environnement"""
    
    def __init__(self, api_manager=None):
        self.api_manager = api_manager
        self.logger = logging.getLogger(__name__)
        self.observations = []
        self.context_understanding = {}
        
    def observe_environment(self) -> Dict[str, Any]:
        """Capture les informations de l'environnement externe et interne"""
        observation = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "api_statuses": self._get_api_statuses(),
            "user_interaction": self._get_user_interaction_state(),
            "external_context": self._get_external_context()
        }
        
        self.observations.append(observation)
        return observation
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Récupère les informations système"""
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_connections": len(psutil.net_connections())
        }
    
    def _get_api_statuses(self) -> Dict[str, bool]:
        """Vérifie le statut des APIs connectées"""
        if not self.api_manager:
            return {}
            
        statuses = {}
        for api_name in self.api_manager.get_active_apis():
            try:
                # Vérification simple du statut
                status = True  # À remplacer par une vérification réelle
                statuses[api_name] = status
            except Exception as e:
                self.logger.warning(f"Erreur lors de la vérification du statut de l'API {api_name}: {e}")
                statuses[api_name] = False
        
        return statuses
    
    def _get_user_interaction_state(self) -> Dict[str, Any]:
        """Analyse l'état d'interaction avec l'utilisateur"""
        # À implémenter: capturer les interactions récentes, patterns, etc.
        return {
            "last_interaction_time": getattr(self, "_last_interaction_time", None),
            "interaction_frequency": getattr(self, "_interaction_frequency", "low"),
            "active_session": True  # À adapter selon le contexte réel
        }
    
    def _get_external_context(self) -> Dict[str, Any]:
        """Récupère le contexte externe (heure, date, actualités, etc.)"""
        context = {
            "datetime": datetime.now().isoformat(),
            "day_of_week": datetime.now().strftime("%A"),
            "time_of_day": self._get_time_of_day()
        }
        
        # Enrichir avec des données externes si les APIs sont disponibles
        if self.api_manager:
            try:
                # Exemple: météo via API OpenMeteo
                from core.api_manager import get_api_instance
                weather_api = get_api_instance(self.api_manager, "openmeteo")
                if weather_api:
                    # Coordonnées par défaut (Paris)
                    forecast = weather_api.get_forecast(48.8566, 2.3522, forecast_days=1)
                    if forecast and isinstance(forecast, dict):
                        context["weather"] = forecast
            except Exception as e:
                self.logger.warning(f"Impossible de récupérer les données météo: {e}")
        
        return context
    
    def _get_time_of_day(self) -> str:
        """Détermine le moment de la journée"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def understand_context(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse l'observation pour en extraire du sens et du contexte"""
        context = {
            "system_load": self._interpret_system_load(observation["system_info"]),
            "connectivity": self._interpret_connectivity(observation["api_statuses"]),
            "user_state": self._interpret_user_state(observation["user_interaction"]),
            "environment": self._interpret_environment(observation["external_context"])
        }
        
        self.context_understanding = context
        return context
    
    def _interpret_system_load(self, system_info: Dict[str, Any]) -> str:
        """Interprète la charge système"""
        cpu = system_info.get("cpu_percent", 0)
        memory = system_info.get("memory_percent", 0)
        
        if cpu > 80 or memory > 80:
            return "critical"
        elif cpu > 60 or memory > 60:
            return "high"
        elif cpu > 30 or memory > 30:
            return "moderate"
        else:
            return "low"
    
    def _interpret_connectivity(self, api_statuses: Dict[str, bool]) -> str:
        """Interprète l'état de connectivité des APIs"""
        if not api_statuses:
            return "unknown"
            
        active_count = sum(1 for status in api_statuses.values() if status)
        total_count = len(api_statuses)
        
        if total_count == 0:
            return "no_apis"
        
        ratio = active_count / total_count
        if ratio >= 0.9:
            return "excellent"
        elif ratio >= 0.7:
            return "good"
        elif ratio >= 0.4:
            return "partial"
        else:
            return "poor"
    
    def _interpret_user_state(self, user_interaction: Dict[str, Any]) -> str:
        """Interprète l'état d'interaction avec l'utilisateur"""
        if not user_interaction.get("active_session", False):
            return "inactive"
            
        last_time = user_interaction.get("last_interaction_time")
        if not last_time:
            return "new_session"
            
        # Analyser le temps écoulé depuis la dernière interaction
        try:
            last_dt = datetime.fromisoformat(last_time)
            now = datetime.now()
            minutes_elapsed = (now - last_dt).total_seconds() / 60
            
            if minutes_elapsed < 5:
                return "actively_engaged"
            elif minutes_elapsed < 15:
                return "recently_active"
            elif minutes_elapsed < 60:
                return "semi_active"
            else:
                return "returning_after_break"
        except:
            return "unknown"
    
    def _interpret_environment(self, external_context: Dict[str, Any]) -> Dict[str, str]:
        """Interprète le contexte externe"""
        context = {
            "time_context": external_context.get("time_of_day", "unknown")
        }
        
        # Interprétation de la météo si disponible
        weather = external_context.get("weather", {})
        if weather:
            try:
                temp = weather.get("current", {}).get("temperature", 0)
                if temp < 5:
                    context["weather_context"] = "very_cold"
                elif temp < 15:
                    context["weather_context"] = "cold"
                elif temp < 25:
                    context["weather_context"] = "moderate"
                elif temp < 32:
                    context["weather_context"] = "warm"
                else:
                    context["weather_context"] = "hot"
            except:
                pass
        
        return context


class CognitiveProcessingModule:
    """Module de traitement cognitif pour l'analyse et la prise de décision"""
    
    def __init__(self, working_memory_capacity: int = 10):
        self.logger = logging.getLogger(__name__)
        self.working_memory = []
        self.working_memory_capacity = working_memory_capacity
        self.attention_focus = None
        self.thought_patterns = []
        
    def process_perception(self, perception_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données de perception pour en extraire des insights"""
        # Mise à jour de la mémoire de travail
        self._update_working_memory({
            "perception": perception_data,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mettre le focus d'attention
        self._focus_attention(perception_data, context)
        
        # Générer des pensées
        thought = self._generate_thought()
        self.thought_patterns.append(thought)
        
        return {
            "focus": self.attention_focus,
            "insight": thought,
            "working_memory_state": len(self.working_memory),
            "processing_result": self._synthesize_processing_result()
        }
    
    def _update_working_memory(self, data: Dict[str, Any]) -> None:
        """Met à jour la mémoire de travail avec de nouvelles données"""
        self.working_memory.append(data)
        
        # Limiter la taille de la mémoire de travail
        if len(self.working_memory) > self.working_memory_capacity:
            self.working_memory.pop(0)  # Enlever le plus ancien élément
    
    def _focus_attention(self, perception: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Détermine sur quoi se concentrer en fonction des entrées"""
        # Algorithme simple de priorisation de l'attention
        priority_areas = []
        
        # Vérifier la charge système
        system_load = context.get("system_load", "unknown")
        if system_load in ["critical", "high"]:
            priority_areas.append(("system_resources", 10))
        
        # Vérifier la connectivité
        connectivity = context.get("connectivity", "unknown")
        if connectivity in ["poor", "partial"]:
            priority_areas.append(("api_connectivity", 8))
        
        # Vérifier l'état de l'utilisateur
        user_state = context.get("user_state", "unknown")
        if user_state in ["actively_engaged", "returning_after_break"]:
            priority_areas.append(("user_interaction", 9))
            
        # Éléments environnementaux particuliers (météo extrême, etc.)
        env = context.get("environment", {})
        weather = env.get("weather_context", "unknown")
        if weather in ["very_cold", "hot"]:
            priority_areas.append(("weather_conditions", 6))
            
        # Choisir le focus d'attention basé sur la priorité
        if priority_areas:
            priority_areas.sort(key=lambda x: x[1], reverse=True)
            self.attention_focus = priority_areas[0][0]
        else:
            # Par défaut, se concentrer sur l'interaction utilisateur
            self.attention_focus = "user_interaction"
    
    def _generate_thought(self) -> Dict[str, Any]:
        """Génère une "pensée" basée sur le focus d'attention et la mémoire de travail"""
        thought = {
            "focus": self.attention_focus,
            "type": "analytical",
            "content": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.attention_focus == "system_resources":
            thought["content"] = self._think_about_system_resources()
            thought["type"] = "problem_solving"
        elif self.attention_focus == "api_connectivity":
            thought["content"] = self._think_about_api_connectivity()
            thought["type"] = "diagnostic"
        elif self.attention_focus == "user_interaction":
            thought["content"] = self._think_about_user_interaction()
            thought["type"] = "empathetic"
        elif self.attention_focus == "weather_conditions":
            thought["content"] = self._think_about_weather()
            thought["type"] = "contextual"
        else:
            # Pensée par défaut
            thought["content"] = "Observation passive de l'environnement"
            thought["type"] = "observational"
            
        return thought
    
    def _think_about_system_resources(self) -> str:
        """Génère une pensée concernant les ressources système"""
        # Analyse des dernières données système dans la mémoire de travail
        high_load_count = 0
        for item in self.working_memory[-3:]:  # 3 derniers éléments
            system_load = item.get("context", {}).get("system_load", "unknown")
            if system_load in ["critical", "high"]:
                high_load_count += 1
        
        if high_load_count >= 2:
            return "Les ressources système sont constamment élevées. Des actions d'optimisation sont nécessaires."
        elif high_load_count == 1:
            return "Pic temporaire de charge système. Surveiller l'évolution."
        else:
            return "Les ressources système sont actuellement sous contrôle."
    
    def _think_about_api_connectivity(self) -> str:
        """Génère une pensée concernant la connectivité des APIs"""
        # Analyser les problèmes de connectivité
        recent_connectivity = [item.get("context", {}).get("connectivity", "unknown") 
                              for item in self.working_memory[-3:]]
        
        if all(conn in ["poor", "partial"] for conn in recent_connectivity):
            return "Problèmes de connectivité persistants. Vérifier la connexion réseau et les endpoints API."
        elif any(conn in ["poor", "partial"] for conn in recent_connectivity):
            return "Connectivité intermittente. Surveiller les timeouts et les erreurs API."
        else:
            return "La connectivité API semble stable actuellement."
    
    def _think_about_user_interaction(self) -> str:
        """Génère une pensée concernant l'interaction utilisateur"""
        # Analyser le pattern d'interaction
        recent_states = [item.get("context", {}).get("user_state", "unknown") 
                        for item in self.working_memory[-3:]]
        
        if "returning_after_break" in recent_states:
            return "L'utilisateur revient après une absence. Proposer un résumé des activités ou changements."
        elif "actively_engaged" in recent_states:
            return "L'utilisateur est activement engagé. Maintenir une réactivité élevée et des réponses pertinentes."
        else:
            return "Interaction utilisateur normale. Rester attentif aux demandes et besoins."
    
    def _think_about_weather(self) -> str:
        """Génère une pensée concernant les conditions météo"""
        # Récupérer la dernière information météo
        for item in reversed(self.working_memory):
            weather = item.get("context", {}).get("environment", {}).get("weather_context", None)
            if weather:
                if weather == "very_cold":
                    return "Conditions météo très froides. Suggérer des contenus adaptés aux activités d'intérieur."
                elif weather == "hot":
                    return "Conditions météo chaudes. Rappeler l'importance de l'hydratation."
                else:
                    return f"Conditions météo {weather}. Pas d'adaptation particulière nécessaire."
        
        return "Pas d'information météo récente disponible."
    
    def _synthesize_processing_result(self) -> Dict[str, Any]:
        """Synthétise les résultats du traitement cognitif"""
        # Analyser les 3 dernières pensées pour dégager une tendance
        recent_thoughts = self.thought_patterns[-3:] if len(self.thought_patterns) >= 3 else self.thought_patterns
        
        focus_areas = {}
        for thought in recent_thoughts:
            focus = thought.get("focus", "unknown")
            focus_areas[focus] = focus_areas.get(focus, 0) + 1
        
        # Déterminer la tendance dominante
        dominant_focus = max(focus_areas.items(), key=lambda x: x[1])[0] if focus_areas else "none"
        
        # Générer une synthèse
        synthesis = {
            "dominant_focus": dominant_focus,
            "thought_variety": len(focus_areas),
            "current_insight": self.thought_patterns[-1]["content"] if self.thought_patterns else None,
            "processing_depth": "deep" if len(recent_thoughts) >= 3 else "shallow",
            "cognitive_state": self._determine_cognitive_state(recent_thoughts)
        }
        
        return synthesis
    
    def _determine_cognitive_state(self, thoughts: List[Dict[str, Any]]) -> str:
        """Détermine l'état cognitif basé sur les pensées récentes"""
        if not thoughts:
            return "inactive"
            
        # Calculer la diversité des types de pensées
        thought_types = set(thought.get("type", "unknown") for thought in thoughts)
        
        if len(thought_types) >= 3:
            return "highly_active"
        elif len(thought_types) >= 2:
            return "active"
        elif "problem_solving" in thought_types or "diagnostic" in thought_types:
            return "focused_analytical"
        elif "empathetic" in thought_types:
            return "focused_social"
        else:
            return "routine"


class AutonomyCognitionSystem:
    """Système de cognition autonome qui intègre perception et traitement"""
    
    def __init__(self, api_manager=None, update_interval: float = 60.0):
        self.logger = logging.getLogger(__name__)
        self.perception = PerceptionModule(api_manager)
        self.cognition = CognitiveProcessingModule()
        self.update_interval = update_interval  # secondes
        self.running = False
        self.cognitive_thread = None
        self.cognitive_state = {}
        self.callbacks = []
        
    def start(self) -> None:
        """Démarre le processus de cognition autonome"""
        if self.running:
            self.logger.warning("Le système de cognition est déjà en cours d'exécution")
            return
            
        self.running = True
        self.cognitive_thread = threading.Thread(target=self._cognitive_loop, daemon=True)
        self.cognitive_thread.start()
        self.logger.info("Système de cognition autonome démarré")
        
    def stop(self) -> None:
        """Arrête le processus de cognition autonome"""
        self.running = False
        if self.cognitive_thread:
            self.cognitive_thread.join(timeout=2.0)
            self.cognitive_thread = None
        self.logger.info("Système de cognition autonome arrêté")
    
    def _cognitive_loop(self) -> None:
        """Boucle principale du processus cognitif"""
        while self.running:
            try:
                # Cycle perception-cognition
                observation = self.perception.observe_environment()
                context = self.perception.understand_context(observation)
                processing_result = self.cognition.process_perception(observation, context)
                
                # Mettre à jour l'état cognitif
                self.cognitive_state = {
                    "observation": observation,
                    "context": context,
                    "processing": processing_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Notifier les observateurs
                self._notify_callbacks()
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle cognitive: {e}")
            
            # Pause avant le prochain cycle
            time.sleep(self.update_interval)
    
    def get_cognitive_state(self) -> Dict[str, Any]:
        """Retourne l'état cognitif actuel"""
        return self.cognitive_state
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Enregistre une fonction de callback à appeler après chaque cycle cognitif"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        """Notifie tous les observateurs enregistrés"""
        for callback in self.callbacks:
            try:
                callback(self.cognitive_state)
            except Exception as e:
                self.logger.error(f"Erreur dans un callback cognitif: {e}")
    
    def get_insight(self) -> Optional[str]:
        """Retourne l'insight actuel du système cognitif"""
        processing = self.cognitive_state.get("processing", {})
        return processing.get("insight", {}).get("content") if processing else None
    
    def get_attention_focus(self) -> Optional[str]:
        """Retourne le focus d'attention actuel"""
        processing = self.cognitive_state.get("processing", {})
        return processing.get("focus") if processing else None


# Fonction utilitaire pour créer une instance du système cognitif
def create_cognition_system(api_manager=None, update_interval: float = 60.0) -> AutonomyCognitionSystem:
    """
    Crée et initialise une instance du système de cognition autonome
    
    Args:
        api_manager: Gestionnaire d'API pour accéder aux services externes
        update_interval: Intervalle de mise à jour en secondes
        
    Returns:
        Instance configurée du système de cognition autonome
    """
    system = AutonomyCognitionSystem(api_manager, update_interval)
    return system
