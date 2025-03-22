#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur de décision pour Polyad
Fournit des capacités de planification stratégique et de prise de décision autonome
"""
import os
import json
import time
import logging
import threading
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class DecisionOption:
    """Représente une option de décision avec ses attributs"""
    
    def __init__(self, action_id: str, description: str, expected_outcomes: Dict[str, float], 
                 resource_cost: float, confidence: float, prerequisites: List[str] = None):
        self.action_id = action_id
        self.description = description
        self.expected_outcomes = expected_outcomes  # {outcome: probability}
        self.resource_cost = resource_cost  # 0.0 - 1.0
        self.confidence = confidence  # 0.0 - 1.0
        self.prerequisites = prerequisites or []
        self.utility_score = 0.0
        
    def calculate_utility(self, goal_alignment: Dict[str, float], risk_tolerance: float) -> float:
        """Calcule l'utilité de cette option en fonction des objectifs et de la tolérance au risque"""
        # Calcul de l'alignement avec les objectifs
        alignment_score = 0.0
        for outcome, probability in self.expected_outcomes.items():
            if outcome in goal_alignment:
                alignment_score += probability * goal_alignment[outcome]
        
        # Ajustement pour la tolérance au risque
        risk_factor = (1.0 - self.confidence) * (1.0 - risk_tolerance)
        cost_factor = self.resource_cost * (1.0 - risk_tolerance)
        
        # Calcul du score final
        self.utility_score = alignment_score * self.confidence - risk_factor - cost_factor
        return self.utility_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'option en dictionnaire"""
        return {
            "action_id": self.action_id,
            "description": self.description,
            "expected_outcomes": self.expected_outcomes,
            "resource_cost": self.resource_cost,
            "confidence": self.confidence,
            "prerequisites": self.prerequisites,
            "utility_score": self.utility_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionOption':
        """Crée une option à partir d'un dictionnaire"""
        option = cls(
            action_id=data["action_id"],
            description=data["description"],
            expected_outcomes=data["expected_outcomes"],
            resource_cost=data["resource_cost"],
            confidence=data["confidence"],
            prerequisites=data.get("prerequisites", [])
        )
        option.utility_score = data.get("utility_score", 0.0)
        return option


class Goal:
    """Représente un objectif avec sa priorité et son état"""
    
    def __init__(self, goal_id: str, description: str, priority: float, 
                 success_criteria: Dict[str, float], deadline: Optional[datetime] = None,
                 parent_goal: Optional[str] = None):
        self.goal_id = goal_id
        self.description = description
        self.priority = priority  # 0.0 - 1.0
        self.success_criteria = success_criteria  # {criterion: threshold}
        self.deadline = deadline
        self.parent_goal = parent_goal
        self.status = "pending"  # pending, active, completed, failed
        self.progress = 0.0  # 0.0 - 1.0
        self.created_at = datetime.now()
        self.completed_at = None
        
    def update_progress(self, progress: float) -> None:
        """Met à jour la progression de l'objectif"""
        self.progress = max(0.0, min(1.0, progress))
        if self.progress >= 1.0:
            self.status = "completed"
            self.completed_at = datetime.now()
        
    def is_expired(self) -> bool:
        """Vérifie si l'objectif a dépassé sa date limite"""
        if self.deadline and datetime.now() > self.deadline:
            if self.status != "completed":
                self.status = "failed"
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objectif en dictionnaire"""
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "success_criteria": self.success_criteria,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "parent_goal": self.parent_goal,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """Crée un objectif à partir d'un dictionnaire"""
        goal = cls(
            goal_id=data["goal_id"],
            description=data["description"],
            priority=data["priority"],
            success_criteria=data["success_criteria"],
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            parent_goal=data.get("parent_goal")
        )
        goal.status = data.get("status", "pending")
        goal.progress = data.get("progress", 0.0)
        goal.created_at = datetime.fromisoformat(data["created_at"])
        goal.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        return goal


class StrategicPlanner:
    """Planificateur stratégique qui définit et gère les objectifs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.goals = {}  # {goal_id: Goal}
        self.goal_hierarchy = {}  # {parent_goal_id: [child_goal_id, ...]}
        self.goal_history = []  # Liste des objectifs passés
        
    def create_goal(self, description: str, priority: float, success_criteria: Dict[str, float],
                   deadline: Optional[datetime] = None, parent_goal: Optional[str] = None) -> str:
        """Crée un nouvel objectif"""
        goal_id = f"goal_{int(time.time())}_{len(self.goals)}"
        goal = Goal(
            goal_id=goal_id,
            description=description,
            priority=priority,
            success_criteria=success_criteria,
            deadline=deadline,
            parent_goal=parent_goal
        )
        
        self.goals[goal_id] = goal
        
        # Ajouter à la hiérarchie si c'est un sous-objectif
        if parent_goal:
            if parent_goal not in self.goal_hierarchy:
                self.goal_hierarchy[parent_goal] = []
            self.goal_hierarchy[parent_goal].append(goal_id)
        
        self.logger.info(f"Nouvel objectif créé: {goal_id} - {description}")
        return goal_id
    
    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """Met à jour la progression d'un objectif"""
        if goal_id not in self.goals:
            self.logger.warning(f"Tentative de mise à jour d'un objectif inexistant: {goal_id}")
            return False
        
        goal = self.goals[goal_id]
        goal.update_progress(progress)
        
        # Si l'objectif est terminé, mettre à jour le parent
        if goal.status == "completed" and goal.parent_goal:
            self._update_parent_goal_progress(goal.parent_goal)
        
        return True
    
    def _update_parent_goal_progress(self, parent_goal_id: str) -> None:
        """Met à jour la progression d'un objectif parent en fonction des sous-objectifs"""
        if parent_goal_id not in self.goals or parent_goal_id not in self.goal_hierarchy:
            return
        
        children = self.goal_hierarchy[parent_goal_id]
        if not children:
            return
        
        # Calculer la progression moyenne des sous-objectifs
        total_progress = sum(self.goals[child_id].progress for child_id in children)
        avg_progress = total_progress / len(children)
        
        # Mettre à jour l'objectif parent
        self.goals[parent_goal_id].update_progress(avg_progress)
    
    def get_active_goals(self) -> List[Goal]:
        """Retourne la liste des objectifs actifs"""
        active_goals = []
        for goal in self.goals.values():
            if goal.status in ["pending", "active"]:
                # Vérifier si l'objectif a expiré
                if goal.is_expired():
                    continue
                active_goals.append(goal)
        
        # Trier par priorité
        active_goals.sort(key=lambda g: g.priority, reverse=True)
        return active_goals
    
    def get_goal_alignment(self, outcomes: List[str]) -> Dict[str, float]:
        """Calcule l'alignement des résultats potentiels avec les objectifs actifs"""
        alignment = {outcome: 0.0 for outcome in outcomes}
        active_goals = self.get_active_goals()
        
        if not active_goals:
            return alignment
        
        # Calculer l'alignement pour chaque résultat
        for outcome in outcomes:
            for goal in active_goals:
                # Vérifier si le résultat correspond à un critère de succès
                for criterion, threshold in goal.success_criteria.items():
                    if criterion.lower() in outcome.lower():
                        alignment[outcome] += threshold * goal.priority
        
        # Normaliser les valeurs
        max_alignment = max(alignment.values(), default=1.0)
        if max_alignment > 0:
            for outcome in alignment:
                alignment[outcome] /= max_alignment
        
        return alignment
    
    def archive_completed_goals(self) -> None:
        """Archive les objectifs terminés ou échoués"""
        to_archive = []
        for goal_id, goal in self.goals.items():
            if goal.status in ["completed", "failed"] or goal.is_expired():
                to_archive.append(goal_id)
                self.goal_history.append(goal.to_dict())
        
        # Supprimer les objectifs archivés
        for goal_id in to_archive:
            if goal_id in self.goals:
                del self.goals[goal_id]
            
            # Supprimer de la hiérarchie
            for parent_id in list(self.goal_hierarchy.keys()):
                if goal_id in self.goal_hierarchy.get(parent_id, []):
                    self.goal_hierarchy[parent_id].remove(goal_id)
                
                # Supprimer les entrées vides
                if not self.goal_hierarchy[parent_id]:
                    del self.goal_hierarchy[parent_id]
    
    def generate_goals_from_insights(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Génère des objectifs basés sur les insights du système cognitif"""
        generated_goals = []
        
        for insight in insights:
            insight_type = insight.get("type", "")
            content = insight.get("content", "")
            focus = insight.get("focus", "")
            
            if not content:
                continue
            
            # Générer un objectif en fonction du type d'insight
            if insight_type == "problem_solving" and "ressources système" in content.lower():
                goal_id = self.create_goal(
                    description=f"Optimiser les ressources système",
                    priority=0.8,
                    success_criteria={"optimisation_système": 0.7, "réduction_charge": 0.8},
                    deadline=datetime.now().replace(hour=23, minute=59, second=59)
                )
                generated_goals.append(goal_id)
                
            elif insight_type == "diagnostic" and "connectivité" in content.lower():
                goal_id = self.create_goal(
                    description=f"Résoudre les problèmes de connectivité API",
                    priority=0.9,
                    success_criteria={"connectivité_stable": 0.9, "réduction_erreurs": 0.8},
                    deadline=datetime.now().replace(hour=23, minute=59, second=59)
                )
                generated_goals.append(goal_id)
                
            elif insight_type == "empathetic" and "utilisateur" in content.lower():
                goal_id = self.create_goal(
                    description=f"Améliorer l'expérience utilisateur",
                    priority=0.7,
                    success_criteria={"satisfaction_utilisateur": 0.9, "réactivité": 0.8},
                    deadline=None  # Objectif continu
                )
                generated_goals.append(goal_id)
        
        return generated_goals


class DecisionMaker:
    """Module de prise de décision qui évalue les options et sélectionne les actions optimales"""
    
    def __init__(self, strategic_planner: StrategicPlanner):
        self.logger = logging.getLogger(__name__)
        self.strategic_planner = strategic_planner
        self.decision_history = []
        self.action_outcomes = {}  # {action_id: outcome}
        self.risk_tolerance = 0.5  # 0.0 (averse) - 1.0 (tolérant)
        self.autonomy_level = 0.5  # 0.0 (supervisé) - 1.0 (totalement autonome)
        
    def evaluate_options(self, options: List[DecisionOption]) -> List[DecisionOption]:
        """Évalue une liste d'options de décision"""
        if not options:
            return []
        
        # Obtenir l'alignement avec les objectifs
        all_outcomes = []
        for option in options:
            all_outcomes.extend(option.expected_outcomes.keys())
        
        goal_alignment = self.strategic_planner.get_goal_alignment(all_outcomes)
        
        # Calculer l'utilité pour chaque option
        for option in options:
            option.calculate_utility(goal_alignment, self.risk_tolerance)
        
        # Trier par score d'utilité
        options.sort(key=lambda o: o.utility_score, reverse=True)
        return options
    
    def select_best_option(self, options: List[DecisionOption]) -> Optional[DecisionOption]:
        """Sélectionne la meilleure option parmi celles évaluées"""
        evaluated_options = self.evaluate_options(options)
        
        if not evaluated_options:
            return None
        
        # Filtrer les options dont les prérequis ne sont pas satisfaits
        valid_options = []
        for option in evaluated_options:
            prerequisites_met = True
            for prereq in option.prerequisites:
                if prereq not in self.action_outcomes:
                    prerequisites_met = False
                    break
            
            if prerequisites_met:
                valid_options.append(option)
        
        if not valid_options:
            return None
        
        # Sélectionner la meilleure option
        best_option = valid_options[0]
        
        # Enregistrer la décision
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "options_evaluated": len(evaluated_options),
            "selected_option": best_option.to_dict(),
            "autonomy_level": self.autonomy_level,
            "risk_tolerance": self.risk_tolerance
        }
        self.decision_history.append(decision_record)
        
        return best_option
    
    def record_outcome(self, action_id: str, outcome: str, success: bool) -> None:
        """Enregistre le résultat d'une action"""
        self.action_outcomes[action_id] = {
            "outcome": outcome,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajuster la tolérance au risque en fonction des résultats
        if success:
            # Augmenter légèrement la tolérance au risque après un succès
            self.risk_tolerance = min(1.0, self.risk_tolerance + 0.05)
        else:
            # Diminuer la tolérance au risque après un échec
            self.risk_tolerance = max(0.1, self.risk_tolerance - 0.1)
    
    def adjust_autonomy_level(self, context: Dict[str, Any]) -> float:
        """Ajuste le niveau d'autonomie en fonction du contexte"""
        # Facteurs influençant l'autonomie
        user_trust = context.get("user_trust", 0.5)  # 0.0 - 1.0
        task_criticality = context.get("task_criticality", 0.5)  # 0.0 - 1.0
        system_reliability = context.get("system_reliability", 0.5)  # 0.0 - 1.0
        
        # Calculer le nouveau niveau d'autonomie
        new_level = (user_trust * 0.4) + (system_reliability * 0.4) - (task_criticality * 0.2)
        new_level = max(0.1, min(1.0, new_level))
        
        # Limiter les changements brusques
        max_change = 0.2
        if abs(new_level - self.autonomy_level) > max_change:
            if new_level > self.autonomy_level:
                new_level = self.autonomy_level + max_change
            else:
                new_level = self.autonomy_level - max_change
        
        self.autonomy_level = new_level
        return self.autonomy_level
    
    def can_act_autonomously(self, option: DecisionOption) -> bool:
        """Détermine si l'agent peut agir de manière autonome pour cette option"""
        # Facteurs à considérer
        option_confidence = option.confidence
        option_cost = option.resource_cost
        
        # Calculer un seuil basé sur le niveau d'autonomie
        threshold = 0.3 + (self.autonomy_level * 0.7)
        
        # L'agent peut agir de manière autonome si la confiance est élevée
        # et que le coût est faible par rapport au niveau d'autonomie
        return option_confidence > threshold and option_cost < self.autonomy_level


class DecisionEngine:
    """Moteur de décision qui intègre planification stratégique et prise de décision"""
    
    def __init__(self, cognition_system=None):
        self.logger = logging.getLogger(__name__)
        self.strategic_planner = StrategicPlanner()
        self.decision_maker = DecisionMaker(self.strategic_planner)
        self.cognition_system = cognition_system
        self.running = False
        self.decision_thread = None
        self.callbacks = []
        
    def start(self, update_interval: float = 60.0) -> None:
        """Démarre le moteur de décision"""
        if self.running:
            self.logger.warning("Le moteur de décision est déjà en cours d'exécution")
            return
            
        self.running = True
        self.decision_thread = threading.Thread(
            target=self._decision_loop, 
            args=(update_interval,),
            daemon=True
        )
        self.decision_thread.start()
        self.logger.info("Moteur de décision démarré")
        
    def stop(self) -> None:
        """Arrête le moteur de décision"""
        self.running = False
        if self.decision_thread:
            self.decision_thread.join(timeout=2.0)
            self.decision_thread = None
        self.logger.info("Moteur de décision arrêté")
    
    def _decision_loop(self, update_interval: float) -> None:
        """Boucle principale du moteur de décision"""
        while self.running:
            try:
                # Archiver les objectifs terminés
                self.strategic_planner.archive_completed_goals()
                
                # Générer de nouveaux objectifs à partir des insights cognitifs
                if self.cognition_system:
                    cognitive_state = self.cognition_system.get_cognitive_state()
                    if cognitive_state:
                        processing = cognitive_state.get("processing", {})
                        insight = processing.get("insight")
                        if insight:
                            self.strategic_planner.generate_goals_from_insights([insight])
                
                # Notifier les observateurs
                self._notify_callbacks()
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de décision: {e}")
            
            # Pause avant le prochain cycle
            time.sleep(update_interval)
    
    def generate_decision_options(self, context: Dict[str, Any]) -> List[DecisionOption]:
        """Génère des options de décision basées sur le contexte"""
        options = []
        
        # Exemple: générer des options basées sur le focus d'attention
        focus = context.get("focus", "")
        
        if focus == "system_resources":
            options.append(DecisionOption(
                action_id=f"optimize_system_{int(time.time())}",
                description="Optimiser l'utilisation des ressources système",
                expected_outcomes={
                    "reduced_cpu_usage": 0.7,
                    "improved_responsiveness": 0.6,
                    "potential_service_disruption": 0.2
                },
                resource_cost=0.3,
                confidence=0.8
            ))
            
            options.append(DecisionOption(
                action_id=f"clear_cache_{int(time.time())}",
                description="Nettoyer le cache système",
                expected_outcomes={
                    "freed_memory": 0.9,
                    "temporary_slowdown": 0.4
                },
                resource_cost=0.2,
                confidence=0.9
            ))
            
        elif focus == "api_connectivity":
            options.append(DecisionOption(
                action_id=f"reconnect_apis_{int(time.time())}",
                description="Rétablir les connexions API",
                expected_outcomes={
                    "restored_connectivity": 0.8,
                    "temporary_service_unavailability": 0.3
                },
                resource_cost=0.4,
                confidence=0.7
            ))
            
            options.append(DecisionOption(
                action_id=f"switch_endpoints_{int(time.time())}",
                description="Basculer vers des endpoints API alternatifs",
                expected_outcomes={
                    "improved_reliability": 0.6,
                    "potential_compatibility_issues": 0.4
                },
                resource_cost=0.5,
                confidence=0.6
            ))
            
        elif focus == "user_interaction":
            options.append(DecisionOption(
                action_id=f"suggest_content_{int(time.time())}",
                description="Suggérer du contenu pertinent à l'utilisateur",
                expected_outcomes={
                    "increased_engagement": 0.7,
                    "user_satisfaction": 0.8
                },
                resource_cost=0.1,
                confidence=0.8
            ))
            
            options.append(DecisionOption(
                action_id=f"summarize_activity_{int(time.time())}",
                description="Résumer l'activité récente pour l'utilisateur",
                expected_outcomes={
                    "improved_awareness": 0.9,
                    "user_appreciation": 0.7
                },
                resource_cost=0.2,
                confidence=0.9
            ))
        
        return options
    
    def make_decision(self, context: Dict[str, Any]) -> Optional[DecisionOption]:
        """Prend une décision basée sur le contexte actuel"""
        # Ajuster le niveau d'autonomie
        self.decision_maker.adjust_autonomy_level(context)
        
        # Générer des options
        options = self.generate_decision_options(context)
        
        # Sélectionner la meilleure option
        best_option = self.decision_maker.select_best_option(options)
        
        return best_option
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Enregistre une fonction de callback à appeler après chaque cycle de décision"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        """Notifie tous les observateurs enregistrés"""
        state = {
            "active_goals": [goal.to_dict() for goal in self.strategic_planner.get_active_goals()],
            "autonomy_level": self.decision_maker.autonomy_level,
            "risk_tolerance": self.decision_maker.risk_tolerance,
            "timestamp": datetime.now().isoformat()
        }
        
        for callback in self.callbacks:
            try:
                callback(state)
            except Exception as e:
                self.logger.error(f"Erreur dans un callback de décision: {e}")


# Fonction utilitaire pour créer une instance du moteur de décision
def create_decision_engine(cognition_system=None) -> DecisionEngine:
    """
    Crée et initialise une instance du moteur de décision
    
    Args:
        cognition_system: Système de cognition pour l'intégration
        
    Returns:
        Instance configurée du moteur de décision
    """
    engine = DecisionEngine(cognition_system)
    return engine
