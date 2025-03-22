from typing import Dict, Any, List, Optional
import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .parallel_processor import ParallelProcessor
from .adaptive_memory import AdaptiveMemory
from .resource_manager import ResourceManager
from .model_manager import ModelManager
from .knowledge_base import KnowledgeBase
from .ollama_client import OllamaClient
from utils.logger import logger

class Polyad:
    """
    Agent autonome d'IA avec capacités d'apprentissage et de traitement parallèle,
    utilisant spécifiquement Ollama avec gemma3:12b-it-q4_K_M
    """
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.processor = ParallelProcessor(num_iterations=6)
        self.memory = AdaptiveMemory(max_tokens=300) 
        self.resources = ResourceManager()
        self.model_manager = ModelManager(host=ollama_host)
        self.knowledge = KnowledgeBase()
        self.ollama_host = ollama_host
        
        # Configurer l'apprentissage spécifiquement pour gemma3:12b-it-q4_K_M
        self.learning_state = {
            'skills': set(),
            'interests': set(),
            'performance_metrics': {},
            'learning_history': [],
            'model_specific': {
                'gemma3:12b-it-q4_K_M': {
                    'optimal_temperature': 0.7,
                    'optimal_max_tokens': 2048,
                    'few_shot_examples': [],
                    'successful_patterns': [],
                    'format_preferences': {},
                    'last_tuned': None
                }
            }
        }
        
    async def initialize(self):
        """Initialize all components and verify system requirements"""
        try:
            # Check system requirements
            system_info = await self.resources.get_system_info()
            if not self._verify_requirements(system_info):
                raise RuntimeError("System does not meet minimum requirements")
            
            # Initialize model based on available resources
            await self.model_manager.initialize(system_info)
            
            # Initialize knowledge base
            await self.knowledge.initialize()
            
            # Load existing state
            await self.load_state()
            
            logger.info("Polyad initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
            
    async def load_state(self):
        """Load saved state"""
        try:
            state_path = os.path.join('data', 'agent_state.json')
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    self.learning_state['skills'] = set(state.get('skills', []))
                    self.learning_state['interests'] = set(state.get('interests', []))
                    self.learning_state['performance_metrics'] = state.get('performance_metrics', {})
                    self.learning_state['learning_history'] = state.get('learning_history', [])
                    
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            
    async def save_state(self):
        """Save current state"""
        try:
            state = {
                'skills': list(self.learning_state['skills']),
                'interests': list(self.learning_state['interests']),
                'performance_metrics': self.learning_state['performance_metrics'],
                'learning_history': self.learning_state['learning_history']
            }
            
            os.makedirs('data', exist_ok=True)
            with open(os.path.join('data', 'agent_state.json'), 'w') as f:
                json.dump(state, f)
                
            # Save other components state
            await self.memory.save_state()
            await self.model_manager.save_stats()
            await self.resources.save_metrics()
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    def _verify_requirements(self, system_info: Dict[str, Any]) -> bool:
        """Verify if system meets minimum requirements"""
        required = {
            'min_cpu_cores': 2,
            'min_ram_gb': 2,
            'min_gpu_memory': 0,  # GPU facultatif
            'supported_os': ['Darwin', 'Linux', 'Windows']
        }
        
        return (
            system_info['cpu_cores'] >= required['min_cpu_cores'] and
            system_info['ram_gb'] >= required['min_ram_gb'] and
            system_info['gpu_memory'] >= required['min_gpu_memory'] and
            system_info['os_type'] in required['supported_os']
        )
        
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter une tâche avec Ollama gemma3:12b-it-q4_K_M"""
        try:
            # Surveiller les ressources
            resources = await self.resources.monitor()
            
            # Sélectionner le modèle approprié (gemma3:12b-it-q4_K_M en priorité)
            model = await self.model_manager.select_model(resources)
            logger.info(f"Utilisation du modèle {model['name']} pour la tâche")
            
            # Vérifier si nous devons apprendre de nouvelles compétences
            required_skills = self._identify_required_skills(task)
            if not required_skills.issubset(self.learning_state['skills']):
                await self._learn_new_skills(required_skills)
            
            # Déterminer les paramètres optimaux pour gemma3:12b-it-q4_K_M
            model_settings = self.learning_state['model_specific'].get(
                'gemma3:12b-it-q4_K_M', 
                {'optimal_temperature': 0.7, 'optimal_max_tokens': 2048}
            )
            
            # Préparer le contexte et les exemples few-shot
            context, examples = self._prepare_context_and_examples(task)
            
            # Traitement selon le type de tâche
            if task.get('type') == 'vision' and 'image' in task:
                # Pour les tâches de vision avec image
                if isinstance(task['image'], list):
                    # Convertir une matrice en image temporaire si nécessaire
                    import numpy as np
                    import cv2
                    img_path = 'temp_image.jpg'
                    cv2.imwrite(img_path, np.array(task['image'], dtype=np.uint8))
                else:
                    img_path = task['image']
                    
                prompt = task.get('prompt', 'Describe this image in detail')
                results = await self.model_manager.process_image(
                    image_path=img_path,
                    prompt=prompt,
                    system=context,
                    temperature=model_settings['optimal_temperature'],
                    max_tokens=model_settings['optimal_max_tokens']
                )
                
            elif task.get('type') == 'chat':
                # Pour les conversations
                messages = task.get('messages', [])
                if not messages:
                    messages = [{'role': 'user', 'content': task.get('prompt', '')}]
                    
                results = await self.model_manager.chat(
                    messages=messages,
                    system=context,
                    temperature=model_settings['optimal_temperature'],
                    max_tokens=model_settings['optimal_max_tokens']
                )
                
            elif task.get('type') == 'embedding':
                # Pour les embeddings
                text = task.get('text', '')
                results = await self.model_manager.get_embeddings(text)
                
            else:
                # Pour les générations de texte standard
                prompt = self._create_prompt(task, examples)
                results = await self.model_manager.generate_response(
                    prompt=prompt,
                    system=context,
                    temperature=model_settings['optimal_temperature'],
                    max_tokens=model_settings['optimal_max_tokens']
                )
            
            # Mettre à jour la base de connaissances avec les résultats
            await self._update_knowledge(task, results)
            
            # Mettre à jour les métriques de performance
            self._update_metrics(task, results)
            
            # Apprentissage continu à partir des résultats
            await self._learn_from_results(task, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Échec du traitement de la tâche: {e}")
            return {'error': str(e)}
            
    def _identify_required_skills(self, task: Dict[str, Any]) -> set:
        """Identify skills required for a task"""
        required_skills = set()
        
        # Analyze task requirements
        if 'vision' in task:
            required_skills.add('computer_vision')
        if 'audio' in task:
            required_skills.add('speech_recognition')
        if 'system' in task:
            required_skills.add('system_operations')
            
        return required_skills
        
    async def _learn_new_skills(self, skills: set):
        """Autonomously learn new skills"""
        for skill in skills:
            if skill not in self.learning_state['skills']:
                logger.info(f"Learning new skill: {skill}")
                
                # Get learning resources
                resources = await self.knowledge.get_learning_resources(skill)
                
                # Practice skill
                success = await self._practice_skill(skill, resources)
                
                if success:
                    self.learning_state['skills'].add(skill)
                    self.learning_state['learning_history'].append({
                        'skill': skill,
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })
                    
    async def _practice_skill(self, skill: str, resources: Dict[str, Any]) -> bool:
        """Practice a new skill until proficiency is achieved"""
        try:
            # Create practice tasks
            tasks = self._create_practice_tasks(skill, resources)
            
            # Practice with increasing difficulty
            for task in tasks:
                result = await self.process_task(task)
                if not self._evaluate_practice(result):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Skill practice failed: {e}")
            return False
            
    def _create_practice_tasks(self, skill: str, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Créer des tâches d'entraînement pour le développement de compétences"""
        tasks = []
        
        # Créer des tâches de difficulté croissante pour gemma3:12b-it-q4_K_M
        for level in range(1, 6):
            task = {
                'type': 'practice', 
                'skill': skill, 
                'difficulty': level, 
                'resources': resources,
                'model': 'gemma3:12b-it-q4_K_M'
            }
            
            # Ajouter des instructions spécifiques selon la compétence
            if skill == 'computer_vision':
                task['prompt'] = f"Analyse cette image au niveau de détail {level}/5."
                task['images'] = [f"data/training/vision/level_{level}_{i}.jpg" for i in range(3)]
            elif skill == 'speech_recognition':
                task['prompt'] = f"Transcris cet audio avec une précision de niveau {level}/5."
                task['audio'] = f"data/training/audio/level_{level}.wav"
            elif skill == 'reasoning':
                task['prompt'] = f"Résous ce problème de raisonnement de niveau {level}/5."
                task['problem'] = resources.get('reasoning_problems', [])[level-1]
            
            tasks.append(task)
            
        return tasks
        
    def _prepare_context_and_examples(self, task: Dict[str, Any]) -> tuple:
        """Préparer le contexte système et les exemples few-shot pour gemma3:12b-it-q4_K_M"""
        # Contexte système par défaut
        context = "Tu es un assistant IA avancé nommé Polyad, basé sur gemma3:12b-it-q4_K_M. "
        context += "Tu excelles dans l'autonomie pour exécuter des tâches complexes. "
        context += "Réponds de manière concise, précise et utile."
        
        # Ajouter des instructions spécifiques selon le type de tâche
        task_type = task.get('type', '')
        
        if task_type == 'vision':
            context += " Analyse les images avec précision, en relevant tous les détails pertinents."
        elif task_type == 'audio':
            context += " Transcris l'audio avec précision et identifie le contexte sonore."
        elif task_type == 'embedding':
            context += " Génère des embeddings de haute qualité qui capturent la sémantique du texte."
        elif task_type == 'reasoning':
            context += " Résous les problèmes étape par étape en expliquant ton raisonnement."
        
        # Récupérer des exemples few-shot pertinents
        examples = self.learning_state['model_specific'].get('gemma3:12b-it-q4_K_M', {}).get('few_shot_examples', [])
        relevant_examples = []
        
        # Filtrer pour ne garder que les exemples pertinents pour cette tâche
        for example in examples:
            if example.get('type') == task_type:
                relevant_examples.append(example)
        
        # Limiter à 3 exemples maximum pour éviter un contexte trop long
        relevant_examples = relevant_examples[:3]
        
        return context, relevant_examples
    
    def _create_prompt(self, task: Dict[str, Any], examples: List[Dict[str, Any]]) -> str:
        """Créer un prompt formaté avec des exemples few-shot"""
        prompt = ""
        
        # Ajouter les exemples few-shot
        if examples:
            prompt += "Voici quelques exemples de tâches similaires:\n\n"
            for i, example in enumerate(examples):
                prompt += f"Exemple {i+1}:\n"
                prompt += f"Input: {example.get('input', '')}\n"
                prompt += f"Output: {example.get('output', '')}\n\n"
        
        # Ajouter la tâche actuelle
        if 'prompt' in task:
            prompt += f"{task['prompt']}\n"
        elif 'instruction' in task:
            prompt += f"{task['instruction']}\n"
        elif 'text' in task:
            prompt += f"{task['text']}\n"
        
        # Ajouter des données supplémentaires si présentes
        if 'data' in task:
            if isinstance(task['data'], dict):
                for key, value in task['data'].items():
                    prompt += f"\n{key}: {value}"
            else:
                prompt += f"\nDonnées: {task['data']}"
        
        return prompt
    
    async def _learn_from_results(self, task: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Apprentissage continu à partir des résultats pour améliorer gemma3:12b-it-q4_K_M"""
        try:
            # Ne pas apprendre des erreurs
            if 'error' in results:
                return
                
            model_settings = self.learning_state['model_specific'].get('gemma3:12b-it-q4_K_M', {})
            
            # Mettre à jour la date du dernier réglage
            model_settings['last_tuned'] = datetime.now().isoformat()
            
            # Enregistrer un exemple few-shot si le résultat est de bonne qualité
            if results.get('usage', {}).get('total_tokens', 0) > 50 and task.get('type'):
                # Créer un nouvel exemple
                example = {
                    'type': task.get('type'),
                    'input': task.get('prompt') or task.get('text') or '',
                    'output': results.get('text') or results.get('message', {}).get('content', ''),
                    'date': datetime.now().isoformat()
                }
                
                # Ajouter à la liste des exemples
                few_shot_examples = model_settings.get('few_shot_examples', [])
                few_shot_examples.append(example)
                
                # Limiter à 50 exemples maximum
                model_settings['few_shot_examples'] = few_shot_examples[-50:]
            
            # Mettre à jour les préférences de format si applicable
            if task.get('type') == 'chat' and results.get('message'):
                format_prefs = model_settings.get('format_preferences', {})
                message_length = len(results['message'].get('content', ''))
                
                # Ajuster les préférences de longueur de réponse
                format_prefs['avg_response_length'] = (
                    format_prefs.get('avg_response_length', message_length) * 0.9 + 
                    message_length * 0.1
                )
                
                model_settings['format_preferences'] = format_prefs
            
            # Sauvegarder les mises à jour
            self.learning_state['model_specific']['gemma3:12b-it-q4_K_M'] = model_settings
            
        except Exception as e:
            logger.error(f"Erreur lors de l'apprentissage: {e}")
    
    def _evaluate_practice(self, result: Dict[str, Any]) -> bool:
        """Évaluer les résultats de l'entraînement"""
        return result.get('success', False) and result.get('score', 0) > 0.8
        
    async def _update_knowledge(self, task: Dict[str, Any], results: Dict[str, Any]):
        """Update knowledge base with new insights"""
        await self.knowledge.add_entry({
            'task': task,
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'performance': self._calculate_performance(results)
        })
        
    def _calculate_performance(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics"""
        return {
            'accuracy': results.get('accuracy', 0),
            'speed': results.get('speed', 0),
            'resource_efficiency': results.get('resource_efficiency', 0)
        }
        
    def _update_metrics(self, task: Dict[str, Any], results: Dict[str, Any]):
        """Update performance metrics"""
        metrics = self._calculate_performance(results)
        
        for metric, value in metrics.items():
            if metric not in self.learning_state['performance_metrics']:
                self.learning_state['performance_metrics'][metric] = []
            self.learning_state['performance_metrics'][metric].append(value)
            
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get current agent capabilities"""
        return {
            'skills': list(self.learning_state['skills']),
            'performance': self.learning_state['performance_metrics'],
            'knowledge_size': len(self.knowledge),
            'resources': self.resources.current_status()
        }
