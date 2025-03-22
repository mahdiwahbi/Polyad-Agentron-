#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système d'apprentissage adaptatif pour Polyad
Fournit des capacités d'apprentissage par renforcement et d'adaptation continue
"""
import os
import json
import time
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class ReinforcementLearningEngine:
    """Moteur d'apprentissage par renforcement pour l'adaptation autonome"""
    
    def __init__(self, alpha: float = 0.1, gamma: float = 0.99, epsilon: float = 0.1):
        """
        Initialise le moteur d'apprentissage
        
        Args:
            alpha: Taux d'apprentissage (0.0 - 1.0)
            gamma: Facteur d'actualisation (0.0 - 1.0)
            epsilon: Epsilon pour l'exploration (0.0 - 1.0)
        """
        self.logger = logging.getLogger(__name__)
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        
        # Table Q pour stocker les valeurs d'action-état
        self.q_table = {}
        
        # Historique des expériences
        self.experience_replay = []
        self.max_replay_size = 10000
        
        # Statistiques d'apprentissage
        self.learning_stats = {
            "total_episodes": 0,
            "success_count": 0,
            "failure_count": 0,
            "average_reward": 0.0,
            "recent_rewards": [],  # Derniers 100 récompenses
            "best_episode_reward": -float('inf')
        }
    
    def get_state_representation(self, state: Dict[str, Any]) -> str:
        """Convertit un état en une représentation utilisable pour la table Q"""
        # Extraire les caractéristiques clés de l'état
        features = [
            str(state.get("system_status", "normal")),
            str(state.get("user_sentiment", "neutral")),
            str(state.get("task_type", "unknown")),
            str(state.get("context_type", "general"))
        ]
        
        # Ajouter les informations d'objectifs actifs
        active_goals = state.get("active_goals", [])
        if active_goals:
            features.extend([goal["goal_id"] for goal in active_goals])
        
        # Créer une représentation unique
        return ":".join(features)
    
    def get_action_value(self, state: str, action: str) -> float:
        """Obtient la valeur Q pour un état-action spécifique"""
        if state not in self.q_table:
            self.q_table[state] = {}
        
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
        
        return self.q_table[state][action]
    
    def update_q_value(self, state: str, action: str, reward: float, 
                      next_state: str, next_action: str = None) -> None:
        """Met à jour la valeur Q pour un état-action spécifique"""
        current_value = self.get_action_value(state, action)
        
        # Calculer la valeur maximale pour l'état suivant
        next_value = 0.0
        if next_state in self.q_table:
            next_values = list(self.q_table[next_state].values())
            if next_values:
                if next_action:
                    next_value = self.get_action_value(next_state, next_action)
                else:
                    next_value = max(next_values)
        
        # Mettre à jour la valeur Q
        new_value = current_value + self.alpha * (
            reward + self.gamma * next_value - current_value
        )
        
        self.q_table[state][action] = new_value
    
    def choose_action(self, state: str, available_actions: List[str]) -> str:
        """Sélectionne une action en utilisant epsilon-greedy"""
        if np.random.rand() < self.epsilon:
            # Exploration: choisir une action aléatoire
            return np.random.choice(available_actions)
        else:
            # Exploitation: choisir l'action avec la valeur Q maximale
            if state in self.q_table:
                action_values = [(a, v) for a, v in self.q_table[state].items()
                               if a in available_actions]
                if action_values:
                    return max(action_values, key=lambda x: x[1])[0]
            
            # Si aucune valeur Q n'est disponible, choisir aléatoirement
            return np.random.choice(available_actions)
    
    def add_experience(self, experience: Dict[str, Any]) -> None:
        """Ajoute une expérience à la mémoire de replay"""
        self.experience_replay.append(experience)
        
        # Maintenir la taille maximale
        if len(self.experience_replay) > self.max_replay_size:
            self.experience_replay.pop(0)
    
    def learn_from_experience(self, batch_size: int = 32) -> float:
        """Apprend d'un échantillon d'expériences"""
        if len(self.experience_replay) < batch_size:
            return 0.0
            
        # Échantillonner aléatoirement des expériences
        batch = np.random.choice(
            self.experience_replay,
            size=min(batch_size, len(self.experience_replay)),
            replace=False
        )
        
        total_loss = 0.0
        for exp in batch:
            state = exp["state"]
            action = exp["action"]
            reward = exp["reward"]
            next_state = exp["next_state"]
            next_action = exp.get("next_action")
            
            # Mettre à jour la valeur Q
            self.update_q_value(state, action, reward, next_state, next_action)
            
            # Calculer la perte (erreur quadratique)
            current_value = self.get_action_value(state, action)
            target_value = reward + self.gamma * self.get_action_value(next_state, next_action or action)
            loss = (target_value - current_value) ** 2
            total_loss += loss
        
        return total_loss / batch_size
    
    def update_learning_stats(self, reward: float, success: bool = False) -> None:
        """Met à jour les statistiques d'apprentissage"""
        self.learning_stats["total_episodes"] += 1
        if success:
            self.learning_stats["success_count"] += 1
        else:
            self.learning_stats["failure_count"] += 1
        
        # Mettre à jour la récompense moyenne
        self.learning_stats["recent_rewards"].append(reward)
        if len(self.learning_stats["recent_rewards"]) > 100:
            self.learning_stats["recent_rewards"].pop(0)
        
        self.learning_stats["average_reward"] = np.mean(self.learning_stats["recent_rewards"])
        
        # Mettre à jour la meilleure récompense
        if reward > self.learning_stats["best_episode_reward"]:
            self.learning_stats["best_episode_reward"] = reward
    
    def save_model(self, filepath: str) -> None:
        """Sauvegarde le modèle d'apprentissage"""
        model_data = {
            "q_table": self.q_table,
            "learning_stats": self.learning_stats,
            "parameters": {
                "alpha": self.alpha,
                "gamma": self.gamma,
                "epsilon": self.epsilon
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """Charge un modèle d'apprentissage pré-entraîné"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
                
            self.q_table = model_data.get("q_table", {})
            self.learning_stats = model_data.get("learning_stats", {
                "total_episodes": 0,
                "success_count": 0,
                "failure_count": 0,
                "average_reward": 0.0,
                "recent_rewards": [],
                "best_episode_reward": -float('inf')
            })
            
            params = model_data.get("parameters", {})
            self.alpha = params.get("alpha", self.alpha)
            self.gamma = params.get("gamma", self.gamma)
            self.epsilon = params.get("epsilon", self.epsilon)
            
            self.logger.info(f"Modèle chargé depuis {filepath}")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du modèle: {e}")

class AdaptiveBehavior:
    """Comportement adaptatif qui ajuste les stratégies en fonction du contexte"""
    
    def __init__(self, rl_engine: ReinforcementLearningEngine):
        self.logger = logging.getLogger(__name__)
        self.rl_engine = rl_engine
        
        # Stratégies d'adaptation
        self.adaptation_strategies = {
            "resource_management": {
                "thresholds": {
                    "low_resources": 0.3,
                    "high_resources": 0.7
                },
                "actions": {
                    "optimize": "optimise_resources",
                    "scale_up": "increase_resources",
                    "scale_down": "decrease_resources"
                }
            },
            "error_handling": {
                "thresholds": {
                    "error_rate": 0.1,
                    "critical_error": 0.05
                },
                "actions": {
                    "retry": "retry_operation",
                    "fallback": "use_fallback",
                    "escalate": "escalate_issue"
                }
            },
            "user_engagement": {
                "thresholds": {
                    "low_engagement": 0.3,
                    "high_engagement": 0.7
                },
                "actions": {
                    "simplify": "simplify_response",
                    "enhance": "enhance_interaction",
                    "personalize": "personalize_experience"
                }
            }
        }
        
        # État d'adaptation
        self.current_strategies = {}
        self.adaptation_history = []
        
    def evaluate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue le contexte et détermine les adaptations nécessaires"""
        adaptations = {}
        
        # Évaluer chaque stratégie d'adaptation
        for strategy_name, strategy in self.adaptation_strategies.items():
            # Obtenir les seuils et les actions pour cette stratégie
            thresholds = strategy["thresholds"]
            actions = strategy["actions"]
            
            # Évaluer les conditions
            if strategy_name == "resource_management":
                system_info = context.get("system_info", {})
                cpu = system_info.get("cpu_percent", 0.0)
                memory = system_info.get("memory_percent", 0.0)
                
                if cpu > thresholds["high_resources"] or memory > thresholds["high_resources"]:
                    adaptations[strategy_name] = actions["scale_up"]
                elif cpu < thresholds["low_resources"] and memory < thresholds["low_resources"]:
                    adaptations[strategy_name] = actions["scale_down"]
                else:
                    adaptations[strategy_name] = actions["optimize"]
            
            elif strategy_name == "error_handling":
                error_rate = context.get("error_rate", 0.0)
                if error_rate > thresholds["critical_error"]:
                    adaptations[strategy_name] = actions["escalate"]
                elif error_rate > thresholds["error_rate"]:
                    adaptations[strategy_name] = actions["fallback"]
                else:
                    adaptations[strategy_name] = actions["retry"]
            
            elif strategy_name == "user_engagement":
                engagement = context.get("user_engagement", 0.5)
                if engagement < thresholds["low_engagement"]:
                    adaptations[strategy_name] = actions["simplify"]
                elif engagement > thresholds["high_engagement"]:
                    adaptations[strategy_name] = actions["enhance"]
                else:
                    adaptations[strategy_name] = actions["personalize"]
        
        return adaptations
    
    def apply_adaptation(self, adaptation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Applique une adaptation spécifique au comportement"""
        result = {
            "adaptation": adaptation,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        # Enregistrer l'adaptation
        self.adaptation_history.append(result)
        
        # Mettre à jour l'état actuel
        self.current_strategies[adaptation] = result
        
        return result
    
    def get_adaptation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retourne l'historique des adaptations"""
        return self.adaptation_history[-limit:]
    
    def get_current_strategies(self) -> Dict[str, Any]:
        """Retourne les stratégies d'adaptation actuelles"""
        return self.current_strategies

class LearningMonitor:
    """Moniteur d'apprentissage qui suit les performances et l'efficacité"""
    
    def __init__(self, rl_engine: ReinforcementLearningEngine):
        self.logger = logging.getLogger(__name__)
        self.rl_engine = rl_engine
        
        # Métriques de performance
        self.performance_metrics = {
            "response_time": [],
            "accuracy": [],
            "resource_usage": [],
            "user_satisfaction": [],
            "task_completion": []
        }
        
        # Seuils de performance
        self.performance_thresholds = {
            "response_time": {
                "warning": 2.0,
                "critical": 5.0
            },
            "accuracy": {
                "warning": 0.8,
                "critical": 0.6
            },
            "resource_usage": {
                "warning": 0.8,
                "critical": 0.9
            },
            "user_satisfaction": {
                "warning": 0.7,
                "critical": 0.5
            },
            "task_completion": {
                "warning": 0.9,
                "critical": 0.7
            }
        }
        
        # Historique des alertes
        self.alert_history = []
        
    def track_performance(self, metric: str, value: float) -> None:
        """Suit une métrique de performance spécifique"""
        if metric in self.performance_metrics:
            self.performance_metrics[metric].append(value)
            
            # Maintenir une fenêtre glissante
            if len(self.performance_metrics[metric]) > 100:
                self.performance_metrics[metric].pop(0)
            
            # Vérifier les seuils et générer des alertes si nécessaire
            self._check_thresholds(metric, value)
    
    def _check_thresholds(self, metric: str, value: float) -> None:
        """Vérifie si une métrique dépasse ses seuils"""
        if metric not in self.performance_thresholds:
            return
            
        thresholds = self.performance_thresholds[metric]
        
        # Pour les métriques où plus est mieux (accuracy, satisfaction, etc.)
        if metric in ["accuracy", "user_satisfaction", "task_completion"]:
            if value < thresholds["warning"]:
                self._generate_alert(metric, value, "warning")
            if value < thresholds["critical"]:
                self._generate_alert(metric, value, "critical")
        
        # Pour les métriques où moins est mieux (response_time, resource_usage)
        else:
            if value > thresholds["warning"]:
                self._generate_alert(metric, value, "warning")
            if value > thresholds["critical"]:
                self._generate_alert(metric, value, "critical")
    
    def _generate_alert(self, metric: str, value: float, severity: str) -> None:
        """Génère une alerte de performance"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "value": value,
            "severity": severity,
            "threshold": self.performance_thresholds[metric][severity]
        }
        
        self.alert_history.append(alert)
        self.logger.warning(f"Alerte de performance: {alert}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Génère un rapport de performance détaillé"""
        report = {
            "metrics": {},
            "alerts": self.alert_history[-10:],  # Dernières 10 alertes
            "learning_stats": self.rl_engine.learning_stats
        }
        
        # Calculer les statistiques pour chaque métrique
        for metric, values in self.performance_metrics.items():
            if values:
                report["metrics"][metric] = {
                    "current": values[-1],
                    "average": np.mean(values),
                    "std_dev": np.std(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return report
    
    def get_learning_efficiency(self) -> float:
        """Calcule l'efficacité d'apprentissage"""
        if not self.rl_engine.learning_stats["total_episodes"]:
            return 0.0
            
        success_rate = self.rl_engine.learning_stats["success_count"] / \
                       self.rl_engine.learning_stats["total_episodes"]
        
        return success_rate

class AdaptiveLearningSystem:
    """Système d'apprentissage adaptatif complet"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rl_engine = ReinforcementLearningEngine()
        self.adaptive_behavior = AdaptiveBehavior(self.rl_engine)
        self.learning_monitor = LearningMonitor(self.rl_engine)
        
        # Configuration
        self.update_interval = 60.0  # secondes
        self.running = False
        self.learning_thread = None
        
    def start(self) -> None:
        """Démarre le système d'apprentissage adaptatif"""
        if self.running:
            self.logger.warning("Le système d'apprentissage est déjà en cours d'exécution")
            return
            
        self.running = True
        self.learning_thread = threading.Thread(
            target=self._learning_loop,
            daemon=True
        )
        self.learning_thread.start()
        self.logger.info("Système d'apprentissage démarré")
    
    def stop(self) -> None:
        """Arrête le système d'apprentissage"""
        self.running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=2.0)
            self.learning_thread = None
        self.logger.info("Système d'apprentissage arrêté")
    
    def _learning_loop(self) -> None:
        """Boucle principale d'apprentissage"""
        while self.running:
            try:
                # Mettre à jour les statistiques d'apprentissage
                self.learning_monitor.get_performance_report()
                
                # Apprendre d'un échantillon d'expériences
                loss = self.rl_engine.learn_from_experience()
                
                # Ajuster le taux d'exploration (epsilon) en fonction de l'efficacité
                efficiency = self.learning_monitor.get_learning_efficiency()
                if efficiency > 0.8:
                    self.rl_engine.epsilon = max(0.05, self.rl_engine.epsilon * 0.95)
                elif efficiency < 0.5:
                    self.rl_engine.epsilon = min(0.3, self.rl_engine.epsilon * 1.05)
                
                # Sauvegarder périodiquement le modèle
                if len(self.rl_engine.experience_replay) > 1000:
                    self.save_model()
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'apprentissage: {e}")
            
            time.sleep(self.update_interval)
    
    def process_experience(self, state: Dict[str, Any], action: str, 
                         reward: float, next_state: Dict[str, Any]) -> None:
        """Traite une expérience d'apprentissage"""
        # Convertir les états en représentations utilisables
        state_rep = self.rl_engine.get_state_representation(state)
        next_state_rep = self.rl_engine.get_state_representation(next_state)
        
        # Ajouter l'expérience à la mémoire de replay
        experience = {
            "state": state_rep,
            "action": action,
            "reward": reward,
            "next_state": next_state_rep
        }
        self.rl_engine.add_experience(experience)
        
        # Mettre à jour les statistiques d'apprentissage
        success = reward > 0
        self.rl_engine.update_learning_stats(reward, success)
        
        # Évaluer le contexte pour les adaptations
        adaptations = self.adaptive_behavior.evaluate_context(state)
        for adaptation in adaptations.values():
            self.adaptive_behavior.apply_adaptation(adaptation, state)
    
    def get_learning_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel du système d'apprentissage"""
        return {
            "rl_engine": self.rl_engine.learning_stats,
            "adaptations": self.adaptive_behavior.get_current_strategies(),
            "performance": self.learning_monitor.get_performance_report(),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_model(self, filepath: str = "adaptive_learning_model.json") -> None:
        """Sauvegarde l'état complet du système d'apprentissage"""
        model_data = {
            "rl_engine": self.rl_engine.q_table,
            "learning_stats": self.rl_engine.learning_stats,
            "adaptation_history": self.adaptive_behavior.adaptation_history,
            "performance_metrics": self.learning_monitor.performance_metrics,
            "alert_history": self.learning_monitor.alert_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, filepath: str = "adaptive_learning_model.json") -> None:
        """Charge un modèle d'apprentissage pré-entraîné"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
                
            self.rl_engine.q_table = model_data.get("rl_engine", {})
            self.rl_engine.learning_stats = model_data.get("learning_stats", {
                "total_episodes": 0,
                "success_count": 0,
                "failure_count": 0,
                "average_reward": 0.0,
                "recent_rewards": [],
                "best_episode_reward": -float('inf')
            })
            
            self.adaptive_behavior.adaptation_history = model_data.get("adaptation_history", [])
            self.learning_monitor.performance_metrics = model_data.get("performance_metrics", {
                "response_time": [],
                "accuracy": [],
                "resource_usage": [],
                "user_satisfaction": [],
                "task_completion": []
            })
            self.learning_monitor.alert_history = model_data.get("alert_history", [])
            
            self.logger.info(f"Modèle d'apprentissage chargé depuis {filepath}")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du modèle d'apprentissage: {e}")


# Fonction utilitaire pour créer une instance du système d'apprentissage
def create_adaptive_learning_system() -> AdaptiveLearningSystem:
    """
    Crée et initialise une instance du système d'apprentissage adaptatif
    
    Returns:
        Instance configurée du système d'apprentissage
    """
    system = AdaptiveLearningSystem()
    return system
