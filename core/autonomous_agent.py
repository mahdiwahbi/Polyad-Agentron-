from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import speech_recognition as sr
import pyautogui
from transformers import AutoTokenizer, AutoModel
import faiss
import torch
import sounddevice as sd
import soundfile as sf
import psutil
import aiohttp

from .polyad import Polyad
from .knowledge_base import KnowledgeBase
from .ollama_client import OllamaClient
from utils.logger import logger

class AutonomousAgent:
    """
    Agent IA autonome avec capacités de vision, audio et action sur macOS.
    Utilise spécifiquement Gemma3:12b-it-q4_K_M via Ollama avec meta-learning et few-shot learning.
    Offre des capacités avancées de traitement multimodal, de raisonnement et d'apprentissage autonome.
    """
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """Initialiser l'agent avec configuration automatique pour Ollama et gemma3:12b-it-q4_K_M"""
        # Core agent avec configuration spécifique pour Ollama
        self.polyad = Polyad(ollama_host=ollama_host)
        self.knowledge = KnowledgeBase()
        self.ollama_host = ollama_host
        
        # Configuration optimisée pour gemma3:12b-it-q4_K_M
        self.model_config = {
            'model': 'gemma3:12b-it-q4_K_M',
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 0.95,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'context_window': 4096
        }
        
        # Client Ollama direct pour certaines opérations
        self.ollama_client = None
        
        # Composants sensoriels
        self.vision = None  # OpenCV pour la vision
        self.audio = None  # Speech recognition
        self.action = None  # PyAutoGUI pour les actions
        
        # Mémoire vectorielle pour RAG (Retrieval Augmented Generation)
        self.vector_store = None
        self.vector_data = {}  # Stockage des documents et leurs IDs
        
        # État d'apprentissage spécifique à gemma3:12b-it-q4_K_M
        self.learning_state = {
            'meta_learning': {
                'strategies': set(),
                'performance': {},
                'best_temperature': 0.7,
                'best_max_tokens': 2048
            },
            'few_shot': {
                'examples': {
                    'vision': [],  # Exemples pour les tâches visuelles
                    'audio': [],  # Exemples pour les tâches audio
                    'reasoning': [],  # Exemples pour les tâches de raisonnement
                    'action': []  # Exemples pour les tâches d'action
                },
                'success_rate': {}
            },
            'contextual': {
                'contexts': {},
                'adaptations': {},
                'persona': "Tu es Polyad, un agent IA autonome capable de perception visuelle, "
                          "traitement audio, exécution d'actions et raisonnement complexe. "
                          "Utilise gemma3:12b-it-q4_K_M pour des réponses précises et concises.",
                'gemma3_strengths': [
                    "Traitement visuel détaillé",
                    "Compréhension contextuelle des conversations",
                    "Génération d'explanations structurées",
                    "Navigation et workflow sur systèmes macOS"
                ]
            },
            'last_tuning': None,
            'task_history': []
        }
        
    async def initialize(self):
        """Initialiser tous les composants avec configuration optimisée pour gemma3:12b-it-q4_K_M"""
        try:
            # Détecter automatiquement le serveur Ollama
            logger.info("Détection du serveur Ollama...")
            ollama_available = await self._detect_ollama_server()
            if not ollama_available:
                raise RuntimeError("Serveur Ollama non disponible")
                
            # Initialiser le client Ollama avec configuration optimisée
            self.ollama_client = OllamaClient(
                host=self.ollama_host,
                model=self.model_config['model'],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens'],
                top_p=self.model_config['top_p'],
                top_k=self.model_config['top_k'],
                repetition_penalty=self.model_config['repetition_penalty']
            )
            
            # Vérifier et configurer le modèle gemma3:12b-it-q4_K_M
            await self._setup_gemma3_model()
            
            # Initialiser Polyad avec configuration optimisée
            if not await self.polyad.initialize(
                model=self.model_config['model'],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens'],
                context_window=self.model_config['context_window']
            ):
                raise RuntimeError("Échec d'initialisation de Polyad")
                
            # Initialiser les composants sensoriels
            await self._initialize_sensors()
            
            # Initialiser la mémoire vectorielle
            await self._initialize_vector_store()
            
            # Charger l'état d'apprentissage
            await self._load_learning_state()
            
            logger.info("Agent autonome initialisé avec succès pour gemma3:12b-it-q4_K_M")
            return True
            
        except Exception as e:
            logger.error(f"Échec d'initialisation: {e}")
            return False
    
    async def _detect_ollama_server(self) -> bool:
        """Détecter automatiquement le serveur Ollama"""
        try:
            # Tester la connexion au serveur Ollama
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.ollama_host}/api/tags") as response:
                        if response.status == 200:
                            logger.info("Serveur Ollama détecté avec succès")
                            return True
                        else:
                            logger.warning(f"Serveur Ollama non accessible (statut: {response.status})")
                            return False
                except aiohttp.ClientError as e:
                    logger.warning(f"Erreur de connexion au serveur Ollama: {e}")
                    return False
        except Exception as e:
            logger.error(f"Erreur lors de la détection du serveur Ollama: {e}")
            return False
    
    async def _setup_gemma3_model(self) -> bool:
        """Configurer le modèle gemma3:12b-it-q4_K_M"""
        try:
            # Vérifier la disponibilité du modèle
            models = await self.ollama_client.list_models()
            model_names = [m.get('name', '') for m in models]
            
            if self.model_config['model'] not in model_names:
                logger.info("Modèle gemma3:12b-it-q4_K_M non trouvé, tentative de téléchargement...")
                
                # Télécharger le modèle
                download_result = await self.ollama_client.pull_model(
                    model=self.model_config['model'],
                    temperature=self.model_config['temperature'],
                    max_tokens=self.model_config['max_tokens'],
                    top_p=self.model_config['top_p'],
                    top_k=self.model_config['top_k'],
                    repetition_penalty=self.model_config['repetition_penalty']
                )
                
                if not download_result:
                    raise RuntimeError("Impossible de télécharger le modèle gemma3:12b-it-q4_K_M")
                    
                logger.info("Modèle gemma3:12b-it-q4_K_M téléchargé avec succès")
            
            # Configurer le modèle avec les paramètres optimisés
            await self.ollama_client.set_model_config(
                model=self.model_config['model'],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens'],
                top_p=self.model_config['top_p'],
                top_k=self.model_config['top_k'],
                repetition_penalty=self.model_config['repetition_penalty']
            )
            
            logger.info("Modèle gemma3:12b-it-q4_K_M configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du modèle: {e}")
            return False
    
    async def _initialize_sensors(self) -> None:
        """Initialiser les composants sensoriels"""
        try:
            # Vision
            self.vision = cv2.VideoCapture(0)
            if not self.vision.isOpened():
                logger.warning("Pas de caméra disponible")
            
            # Audio
            self.audio = sr.Recognizer()
            self.audio.energy_threshold = 4000  # Plus sensible pour gemma3
            self.audio.dynamic_energy_threshold = True  # Adaptation automatique
            
            # Actions
            pyautogui.FAILSAFE = True
            
            logger.info("Composants sensoriels initialisés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des composants sensoriels: {e}")
    
    async def _initialize_vector_store(self) -> None:
        """Initialiser la mémoire vectorielle"""
        try:
            # Initialiser avec la dimension optimale pour gemma3
            embedding_dim = 768
            self.vector_store = faiss.IndexFlatL2(embedding_dim)
            
            # Créer le répertoire pour la persistance
            os.makedirs('data/vector_store', exist_ok=True)
            
            # Charger la mémoire vectorielle existante si disponible
            index_path = os.path.join('data/vector_store', 'vector_store.index')
            if os.path.exists(index_path):
                self.vector_store = faiss.read_index(index_path)
                logger.info("Mémoire vectorielle chargée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la mémoire vectorielle: {e}")
            
    async def process_visual(self, image_path: Optional[str] = None, prompt: str = "Analyse cette image en détail"):
        """Traiter une entrée visuelle avec gemma3:12b-it-q4_K_M"""
        try:
            start_time = time.time()
            
            # Gérer l'image en fonction de la source
            if image_path:
                frame = cv2.imread(image_path)
                if frame is None:
                    raise FileNotFoundError(f"Image non trouvée: {image_path}")
            else:
                if not self.vision or not self.vision.isOpened():
                    self.vision = cv2.VideoCapture(0)
                    if not self.vision.isOpened():
                        raise RuntimeError("Caméra non disponible")
                
                ret, frame = self.vision.read()
                if not ret:
                    raise RuntimeError("Échec de capture d'image")
                
                # Sauvegarde temporaire pour l'analyse
                temp_image_path = "temp_capture.jpg"
                cv2.imwrite(temp_image_path, frame)
                image_path = temp_image_path
                    
            # Prétraitement adapté à gemma3:12b-it-q4_K_M
            processed_frame = cv2.resize(frame, (512, 512))
            
            # Récupérer des contextes d'exemples similaires
            similar_examples = self._get_relevant_examples('vision', 2)
            context = self._build_vision_context(similar_examples)
            
            # Analyse avec gemma3:12b-it-q4_K_M via Polyad
            result = await self.polyad.process_task({
                'type': 'vision',
                'image': image_path,
                'prompt': prompt,
                'timestamp': datetime.now().isoformat(),
                'system': context
            })
            
            # Enregistrer cette expérience pour amélioration future
            if 'error' not in result:
                self._save_example('vision', {
                    'input': prompt,
                    'image': image_path if image_path != "temp_capture.jpg" else None,
                    'output': result.get('text') or result.get('message', {}).get('content', ''),
                    'time': time.time() - start_time,
                    'date': datetime.now().isoformat()
                })
            
            # Nettoyer l'image temporaire si créée
            if image_path == "temp_capture.jpg" and os.path.exists(image_path):
                os.remove(image_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur de traitement visuel: {e}")
            return {'error': str(e)}
            
    async def process_audio(self, audio_path: Optional[str] = None, duration: int = 5, prompt: str = "Transcris et analyse cet audio"):
        """Traiter une entrée audio avec gemma3:12b-it-q4_K_M"""
        try:
            start_time = time.time()
            temp_file = None
            text = ""
            
            # Gérer la source audio
            if audio_path:
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"Fichier audio non trouvé: {audio_path}")
                audio_file_path = audio_path
            else:
                # Enregistrer l'audio en temps réel
                logger.info(f"Enregistrement audio pendant {duration} secondes...")
                audio_data = sd.rec(
                    int(duration * 44100),
                    samplerate=44100,
                    channels=1,
                    dtype='float32'
                )
                sd.wait()
                
                # Sauvegarder temporairement
                temp_file = 'temp_audio.wav'
                sf.write(temp_file, audio_data, 44100)
                audio_file_path = temp_file
            
            # Reconnaissance vocale optimisée pour gemma3:12b-it-q4_K_M
            with sr.AudioFile(audio_file_path) as source:
                # Ajustement de la sensibilité pour une meilleure transcription
                audio = self.audio.record(source)
                
                # Essayer d'abord avec Whisper si disponible via Ollama
                try:
                    # Vérifier si gemma3 peut transcrire directement l'audio
                    logger.info("Tentative de transcription directe via Ollama...")
                    # Pour le moment, on utilise Google comme fallback mais idéalement gemma3
                    # pourrait traiter l'audio directement
                    text = self.audio.recognize_google(audio, language="fr-FR")
                except:
                    # Fallback à Google Speech Recognition
                    logger.info("Fallback à Google Speech Recognition")
                    text = self.audio.recognize_google(audio)
            
            # Récupérer des exemples pertinents pour le contexte
            similar_examples = self._get_relevant_examples('audio', 2)
            context = self._build_audio_context(similar_examples)
            
            # Traiter avec gemma3:12b-it-q4_K_M via Polyad
            result = await self.polyad.process_task({
                'type': 'chat',  # On utilise le chat pour l'audio transcrit
                'messages': [
                    {
                        'role': 'system',
                        'content': context
                    },
                    {
                        'role': 'user',
                        'content': f"{prompt}\n\nTranscription: {text}"
                    }
                ],
                'timestamp': datetime.now().isoformat()
            })
            
            # Enregistrer cette expérience pour amélioration future
            if 'error' not in result:
                self._save_example('audio', {
                    'input': text,
                    'output': result.get('message', {}).get('content', ''),
                    'time': time.time() - start_time,
                    'date': datetime.now().isoformat()
                })
                
            # Nettoyer si fichier temporaire
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur de traitement audio: {e}")
            return {'error': str(e)}
            
    async def execute_action(self, action: Dict[str, Any]):
        """Exécuter une action sur macOS avec validation via gemma3:12b-it-q4_K_M"""
        try:
            start_time = time.time()
            action_type = action.get('type')
            
            # Vérification de sécurité via gemma3:12b-it-q4_K_M pour les actions sensibles
            if action_type in ['system', 'keypress', 'sequence']:
                # Utiliser gemma3 pour valider que l'action est sécurisée
                security_check = await self.polyad.process_task({
                    'type': 'chat',
                    'messages': [
                        {
                            'role': 'system',
                            'content': "Tu es un agent de sécurité responsable de la validation d'actions. "
                                        "Réponds uniquement par 'SAFE' ou 'UNSAFE' suivi d'une brève explication."
                        },
                        {
                            'role': 'user',
                            'content': f"Est-ce que cette action est sécurisée pour un exécution automatique sur macOS? {json.dumps(action)}"
                        }
                    ]
                })
                
                response = security_check.get('message', {}).get('content', '')
                if response.startswith('UNSAFE') or 'UNSAFE' in response:
                    logger.warning(f"Action bloquée pour raison de sécurité: {response}")
                    return {
                        'success': False,
                        'error': 'Action refusée pour raison de sécurité',
                        'details': response
                    }
            
            # Exécution des différents types d'actions
            result = {'success': True}
            
            if action_type == 'click':
                x, y = action['coordinates']
                pyautogui.click(x, y)
                result['action'] = f"Click aux coordonnées ({x}, {y})"
                
            elif action_type == 'move':
                x, y = action['coordinates']
                pyautogui.moveTo(x, y, duration=action.get('duration', 0.5))
                result['action'] = f"Déplacement aux coordonnées ({x}, {y})"
                
            elif action_type == 'type':
                text = action['text']
                pyautogui.write(text, interval=action.get('interval', 0.05))
                result['action'] = f"Saisie du texte: {text[:20]}{'...' if len(text) > 20 else ''}"
                
            elif action_type == 'keypress':
                key = action['key']
                pyautogui.press(key)
                result['action'] = f"Appui sur la touche: {key}"
                
            elif action_type == 'shortcut':
                keys = action['keys']
                pyautogui.hotkey(*keys)
                result['action'] = f"Raccourci clavier: {'+'.join(keys)}"
                
            elif action_type == 'sequence':
                # Exécuter une séquence d'actions
                sequence = action['sequence']
                sequence_results = []
                
                for seq_action in sequence:
                    seq_result = await self.execute_action(seq_action)
                    sequence_results.append(seq_result)
                    if not seq_result.get('success', False):
                        # Arrêter en cas d'échec dans la séquence
                        break
                    
                    # Pause entre les actions
                    await asyncio.sleep(action.get('delay', 0.2))
                    
                result['sequence_results'] = sequence_results
                result['action'] = f"Séquence de {len(sequence)} actions"
                result['success'] = all(r.get('success', False) for r in sequence_results)
                
            elif action_type == 'system':
                # Exécution de commande système avec restrictions strictes
                if self._is_safe_command(action['command']):
                    import subprocess
                    proc = subprocess.run(
                        action['command'],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=action.get('timeout', 10)
                    )
                    result['returncode'] = proc.returncode
                    result['output'] = proc.stdout
                    result['error_output'] = proc.stderr
                    result['action'] = f"Commande système: {action['command'][:30]}{'...' if len(action['command']) > 30 else ''}"
                    result['success'] = proc.returncode == 0
                else:
                    raise ValueError(f"Commande système non autorisée: {action['command']}")
                
            else:
                raise ValueError(f"Type d'action inconnu: {action_type}")
            
            # Enregistrer cette expérience pour amélioration future
            execution_time = time.time() - start_time
            if result['success']:
                self._save_example('action', {
                    'action': action,
                    'result': result,
                    'time': execution_time,
                    'date': datetime.now().isoformat()
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur d'exécution d'action: {e}")
            return {'success': False, 'error': str(e)}
    
    def _is_safe_command(self, command: str) -> bool:
        """Vérifier si une commande système est sécurisée pour l'exécution"""
        # Liste des commandes autorisées 
        allowed_commands = ['ls', 'ps', 'pwd', 'echo', 'whoami', 'date', 'uptime']
        
        # Vérifier si la commande commence par une commande autorisée
        command_parts = command.strip().split()
        if not command_parts:
            return False
            
        base_command = command_parts[0]
        if base_command not in allowed_commands:
            return False
            
        # Vérifier l'absence de caractères dangereux
        dangerous_chars = [';', '&', '|', '>', '<', '`', '$', '\\', '"', "'", '*']
        return not any(char in command for char in dangerous_chars)
            
    async def learn_from_experience(self, experience: Dict[str, Any]):
        """Apprendre de l'expérience via meta-learning avec gemma3:12b-it-q4_K_M"""
        try:
            # Vérifier si l'expérience contient les données nécessaires
            if not experience.get('task_id') or not experience.get('data'):
                raise ValueError("Expérience incomplète: task_id et data requis")
                
            # Formater l'expérience pour gemma3:12b-it-q4_K_M
            formatted_experience = self._format_experience_for_learning(experience)
            
            # Extraire les patterns avec l'aide de gemma3:12b-it-q4_K_M
            patterns_response = await self.polyad.process_task({
                'type': 'chat',
                'messages': [
                    {
                        'role': 'system',
                        'content': "Tu es un analyste IA qui extrait des patterns d'apprentissage. "
                                    "Identifie les patterns réutilisables dans cette expérience et liste-les au format JSON."
                    },
                    {
                        'role': 'user',
                        'content': f"Analyse cette expérience et extrais les patterns d'apprentissage:\n{json.dumps(formatted_experience, indent=2)}"
                    }
                ]
            })
            
            # Extraire le JSON généré par gemma3
            patterns_content = patterns_response.get('message', {}).get('content', '')
            try:
                # Chercher le bloc JSON dans la réponse
                import re
                json_pattern = r'```json\n(.+?)\n```'  # Extraire le JSON entre à partir des indicateurs markdown
                json_match = re.search(json_pattern, patterns_content, re.DOTALL)
                
                if json_match:
                    patterns_json = json_match.group(1)
                    patterns = json.loads(patterns_json)
                else:
                    # Essayer de trouver un JSON sans les marqueurs code
                    json_pattern = r'\{.*\}'  # Pattern simplifié pour JSON
                    json_match = re.search(json_pattern, patterns_content, re.DOTALL)
                    if json_match:
                        patterns = json.loads(json_match.group(0))
                    else:
                        patterns = self._extract_patterns(experience)  # Fallback
            except:
                # Fallback à l'extraction manuelle
                patterns = self._extract_patterns(experience)
            
            # Mettre à jour les stratégies
            self.learning_state['meta_learning']['strategies'].update(set(patterns) if isinstance(patterns, list) else {str(patterns)})
            
            # Évaluer la performance avec des critères adaptés à gemma3:12b-it-q4_K_M
            performance = await self._evaluate_performance_with_gemma3(experience)
            
            # Mettre à jour les métriques de performance
            self.learning_state['meta_learning']['performance'][experience['task_id']] = performance
            
            # Générer l'embedding avec gemma3:12b-it-q4_K_M
            try:
                embedding_result = await self.polyad.process_task({
                    'type': 'embedding',
                    'text': json.dumps(formatted_experience)
                })
                embedding = embedding_result.get('embedding', [])
                
                if embedding and len(embedding) > 0:
                    # Convertir en numpy array
                    import numpy as np
                    embedding_np = np.array([embedding], dtype=np.float32)
                    
                    # Générer un ID unique pour cette expérience
                    experience_id = len(self.vector_data)
                    
                    # Stocker les données associées à cet embedding
                    self.vector_data[experience_id] = formatted_experience
                    
                    # Ajouter l'embedding à l'index
                    self.vector_store.add(embedding_np)
            except Exception as e:
                logger.error(f"Erreur lors de la génération de l'embedding: {e}")
            
            # Sauvegarder l'état d'apprentissage
            await self._save_learning_state()
            
            return {'success': True, 'performance': performance}
            
        except Exception as e:
            logger.error(f"Erreur d'apprentissage: {e}")
            return {'error': str(e)}
            
    def _extract_patterns(self, experience: Dict[str, Any]) -> set:
        """Extraire des patterns d'une expérience (méthode de secours)"""
        patterns = set()
        
        # Analyser la structure de la tâche
        if 'steps' in experience:
            pattern = tuple(step['type'] for step in experience['steps'])
            patterns.add(f"workflow:{pattern}")
            
        # Analyser le contexte
        if 'context' in experience:
            context_pattern = (
                experience['context'].get('location'),
                experience['context'].get('time_of_day')
            )
            patterns.add(f"context:{context_pattern}")
            
        # Ajouter des patterns basés sur le type de tâche
        if 'task_type' in experience:
            patterns.add(f"task_type:{experience['task_type']}")
            
        # Extraire des patterns des données
        if 'data' in experience:
            data = experience['data']
            if isinstance(data, dict):
                for key in data.keys():
                    patterns.add(f"pattern:{key}")
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    for item in data:
                        for key in item.keys():
                            patterns.add(f"pattern:{key}")
                else:
                    patterns.add(f"pattern:list_item")
                    
        return patterns
        
    def _format_experience_for_learning(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Formater l'expérience pour l'apprentissage par gemma3:12b-it-q4_K_M"""
        # Ne garder que les données pertinentes et structurer pour l'apprentissage
        formatted = {
            'task_id': experience.get('task_id', ''),
            'task_type': experience.get('task_type', ''),
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }
        
        # Structure différente selon le type de données
        data = experience.get('data', {})
        if isinstance(data, dict):
            # Aplatir les structures de données profondément imbriquées
            for key, value in data.items():
                if isinstance(value, dict) and len(value) > 10:
                    # Résumer les dictionnaires volumineux
                    formatted['data'][key] = {
                        'type': 'dict_summary',
                        'keys': list(value.keys())[:10],
                        'size': len(value)
                    }
                elif isinstance(value, list) and len(value) > 10:
                    # Résumer les listes volumineuses
                    formatted['data'][key] = {
                        'type': 'list_summary',
                        'sample': value[:5],
                        'size': len(value)
                    }
                else:
                    formatted['data'][key] = value
        else:
            formatted['data'] = {'raw': str(data)[:1000]}  # Limiter la taille
        
        # Ajouter les métadonnées de l'expérience
        if 'metadata' in experience:
            formatted['metadata'] = experience.get('metadata', {})
        
        # Ajouter les résultats s'ils existent
        if 'results' in experience:
            results = experience['results']
            if isinstance(results, dict):
                formatted['results'] = {
                    k: v for k, v in results.items() 
                    if k not in ['raw_output', 'debug_info']
                }
            else:
                formatted['results'] = {'summary': str(results)[:1000]}
        
        return formatted
        
    async def _evaluate_performance_with_gemma3(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluer la performance de l'expérience avec l'aide de gemma3:12b-it-q4_K_M"""
        try:
            # Préparer une version formatée de l'expérience pour l'évaluation
            eval_data = self._format_experience_for_learning(experience)
            
            # Obtenir une évaluation générée par gemma3:12b-it-q4_K_M
            eval_response = await self.polyad.process_task({
                'type': 'chat',
                'messages': [
                    {
                        'role': 'system',
                        'content': "Tu es un évaluateur de performance IA. "
                                    "Analyse cette expérience et évalue sa performance selon plusieurs métriques. "
                                    "Retourne ton évaluation au format JSON avec un score global entre 0.0 et 1.0 "
                                    "et des scores individuels pour précision, efficacité et innovation."
                    },
                    {
                        'role': 'user',
                        'content': f"Analyse et évalue la performance de cette expérience:\n{json.dumps(eval_data, indent=2)}"
                    }
                ]
            })
            
            # Extraire l'évaluation du JSON généré par gemma3
            eval_content = eval_response.get('message', {}).get('content', '')
            
            try:
                # Extraire le JSON de la réponse
                import re
                json_pattern = r'```json\n(.+?)\n```'  # Chercher le JSON entre marqueurs markdown
                json_match = re.search(json_pattern, eval_content, re.DOTALL)
                
                if json_match:
                    eval_json = json_match.group(1)
                    evaluation = json.loads(eval_json)
                else:
                    # Chercher sans les marqueurs code
                    json_pattern = r'\{.*\}'  # Pattern simplifié pour JSON
                    json_match = re.search(json_pattern, eval_content, re.DOTALL)
                    if json_match:
                        evaluation = json.loads(json_match.group(0))
                    else:
                        # Fallback à une évaluation de base
                        return self._evaluate_performance_fallback(experience)
                        
                # Vérifier que le format est correct
                if 'score' not in evaluation:
                    evaluation['score'] = 0.5  # Valeur par défaut
                    
                # Assurer que les métriques sont présentes
                if 'metrics' not in evaluation:
                    evaluation['metrics'] = {}
                    
                return evaluation
                
            except Exception as e:
                logger.error(f"Erreur lors du parsing de l'évaluation: {e}")
                return self._evaluate_performance_fallback(experience)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation avec gemma3: {e}")
            return self._evaluate_performance_fallback(experience)
            
    def _evaluate_performance_fallback(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluer la performance de l'expérience (méthode de secours)"""
        # Évaluation de base si gemma3 échoue
        performance = {
            'score': 0.5,  # Score neutre par défaut
            'metrics': {
                'accuracy': 0.5,
                'efficiency': 0.5,
                'innovation': 0.5
            }
        }
        
        # Vérifier si l'expérience a réussi
        if 'success' in experience:
            success = experience['success']
            performance['score'] = 0.8 if success else 0.2
            performance['metrics']['accuracy'] = 0.8 if success else 0.3
            
        # Vérifier le temps d'exécution pour l'efficacité
        if 'time_taken' in experience:
            exec_time = experience['time_taken']
            if exec_time < 1.0:  # Moins d'une seconde
                performance['metrics']['efficiency'] = 0.9
            elif exec_time < 5.0:  # Moins de 5 secondes
                performance['metrics']['efficiency'] = 0.7
            else:  # Plus lent
                performance['metrics']['efficiency'] = 0.5
                
        # Mesurer l'innovation basée sur la nouveauté des patterns
        if 'task_type' in experience:
            # Si c'est un type de tâche peu fréquent
            task_count = sum(1 for task in self.learning_state['task_history'] 
                           if task.get('task_type') == experience['task_type'])
            if task_count < 3:  # Tâche rare
                performance['metrics']['innovation'] = 0.8
            
        return performance
        
    def _get_relevant_examples(self, task_type: str, count: int = 3) -> List[Dict[str, Any]]:
        """Récupérer les exemples les plus pertinents pour un type de tâche donné"""
        # Obtenir les exemples pour ce type de tâche
        examples = self.learning_state['few_shot']['examples'].get(task_type, [])
        
        if not examples:
            return []  # Aucun exemple disponible
            
        # Trier par date (du plus récent au plus ancien)
        sorted_examples = sorted(
            examples, 
            key=lambda x: x.get('date', ''), 
            reverse=True
        )
        
        # Limiter au nombre demandé
        return sorted_examples[:count]
    
    def _build_vision_context(self, examples: List[Dict[str, Any]]) -> str:
        """Construire un contexte système pour les tâches de vision"""
        context = self.learning_state['contextual']['persona'] + "\n\n"
        context += "Pour les tâches de vision, analyse les images en détail avec ces points particuliers:\n"
        context += "- Description des éléments visuels principaux\n"
        context += "- Identification des objets, personnes ou textes visibles\n"
        context += "- Analyse des couleurs, éclairages et compositions\n"
        context += "- Interprétation du contexte de l'image\n"
        
        # Ajouter des exemples si disponibles
        if examples:
            context += "\nVoici des exemples d'analyses similaires:\n"
            for i, example in enumerate(examples, 1):
                context += f"\nExemple {i}:\n"
                context += f"Prompt: {example.get('input', '')}\n"
                context += f"Analyse: {example.get('output', '')}\n"
        
        return context
    
    def _build_audio_context(self, examples: List[Dict[str, Any]]) -> str:
        """Construire un contexte système pour les tâches audio"""
        context = self.learning_state['contextual']['persona'] + "\n\n"
        context += "Pour les tâches de transcription et analyse audio, priorise:\n"
        context += "- Précision et correction des erreurs de transcription\n"
        context += "- Identification du contexte de la conversation\n"
        context += "- Détection des intentions et émotions du locuteur\n"
        context += "- Respect des conventions linguistiques et de la ponctuation\n"
        
        # Ajouter des exemples si disponibles
        if examples:
            context += "\nVoici des exemples d'analyses similaires:\n"
            for i, example in enumerate(examples, 1):
                context += f"\nExemple {i}:\n"
                context += f"Transcription: {example.get('input', '')}\n"
                context += f"Analyse: {example.get('output', '')}\n"
        
        return context
    
    def _save_example(self, example_type: str, example_data: Dict[str, Any]) -> None:
        """Sauvegarder un exemple pour l'apprentissage futur"""
        # S'assurer que le type d'exemple existe
        if example_type not in self.learning_state['few_shot']['examples']:
            self.learning_state['few_shot']['examples'][example_type] = []
            
        # Ajouter l'exemple à la liste
        examples = self.learning_state['few_shot']['examples'][example_type]
        examples.append(example_data)
        
        # Limiter le nombre d'exemples (garder les 50 plus récents)
        if len(examples) > 50:
            examples = sorted(examples, key=lambda x: x.get('date', ''), reverse=True)[:50]
            self.learning_state['few_shot']['examples'][example_type] = examples
            
        # Mettre à jour la date de dernier ajustement
        self.learning_state['last_tuning'] = datetime.now().isoformat()
        
    async def save_state(self):
        """Sauvegarder l'état de l'agent"""
        try:
            # Sauvegarder l'état d'apprentissage
            state = {
                'meta_learning': {
                    'strategies': list(self.learning_state['meta_learning']['strategies']),
                    'performance': self.learning_state['meta_learning']['performance']
                },
                'few_shot': self.learning_state['few_shot'],
                'contextual': self.learning_state['contextual']
            }
            
            os.makedirs('data', exist_ok=True)
            with open(os.path.join('data', 'agent_state.json'), 'w') as f:
                json.dump(state, f)
                
            # Sauvegarder la mémoire vectorielle
            faiss.write_index(
                self.vector_store,
                os.path.join('data', 'vector_store.index')
            )
            
            # Sauvegarder l'état Polyad
            await self.polyad.save_state()
            
            logger.info("État de l'agent sauvegardé")
            
        except Exception as e:
            logger.error(f"Erreur de sauvegarde: {e}")
            
    async def _save_learning_state(self, path: str = 'data/learning_state.json'):
        """Sauvegarder l'état d'apprentissage dans un fichier"""
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Convertir les ensembles en listes pour la sérialisation JSON
            serializable_state = json.loads(json.dumps(self.learning_state, default=lambda o: list(o) if isinstance(o, set) else o))
            
            # Écrire dans le fichier
            with open(path, 'w') as f:
                json.dump(serializable_state, f, indent=2)
                
            logger.info(f"État d'apprentissage sauvegardé dans {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'état d'apprentissage: {e}")
            return False
            
    async def _load_learning_state(self, path: str = 'data/learning_state.json'):
        """Charger l'état d'apprentissage depuis un fichier"""
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    loaded_state = json.load(f)
                    
                # Convertir les listes en ensembles si nécessaire
                if 'meta_learning' in loaded_state and 'strategies' in loaded_state['meta_learning']:
                    loaded_state['meta_learning']['strategies'] = set(loaded_state['meta_learning']['strategies'])
                    
                # Mettre à jour l'état avec les données chargées
                for key in loaded_state:
                    if key in self.learning_state:
                        if isinstance(loaded_state[key], dict) and isinstance(self.learning_state[key], dict):
                            self.learning_state[key].update(loaded_state[key])
                        else:
                            self.learning_state[key] = loaded_state[key]
                            
                logger.info(f"État d'apprentissage chargé depuis {path}")
                return True
            else:
                logger.info("Aucun état d'apprentissage existant trouvé")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'état d'apprentissage: {e}")
            return False
            
    async def query_knowledge(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Interroger la base de connaissances en utilisant gemma3:12b-it-q4_K_M"""
        try:
            # Générer l'embedding de la requête avec gemma3
            embedding_result = await self.polyad.process_task({
                'type': 'embedding',
                'text': query
            })
            
            query_embedding = embedding_result.get('embedding', [])
            if not query_embedding:
                logger.error("Impossible d'obtenir un embedding pour la requête")
                return []
                
            # Convertir en numpy array
            import numpy as np
            query_np = np.array([query_embedding], dtype=np.float32)
            
            # Rechercher les documents similaires
            if self.vector_store.ntotal == 0:
                logger.warning("Aucune donnée dans la mémoire vectorielle")
                return []
                
            distances, indices = self.vector_store.search(query_np, min(k, self.vector_store.ntotal))
            
            # Récupérer les documents correspondants
            results = []
            for i, idx in enumerate(indices[0]):
                if idx in self.vector_data:
                    result = self.vector_data[idx].copy()
                    result['similarity_score'] = float(1.0 - distances[0][i])  # Convertir la distance en score de similarité
                    results.append(result)
                    
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la requête de connaissances: {e}")
            return []
            
    async def load_state(self):
        """Charger l'état de l'agent"""
        try:
            # Charger l'état d'apprentissage
            await self._load_learning_state()
            
            # Charger la mémoire vectorielle
            vector_path = os.path.join('data', 'vector_store.index')
            if os.path.exists(vector_path):
                self.vector_store = faiss.read_index(vector_path)
                
            # Charger l'état Polyad
            await self.polyad.load_state()
            
        except Exception as e:
            logger.error(f"Erreur de chargement: {e}")
            
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Obtenir les capacités actuelles de l'agent"""
        return {
            'vision': self.vision is not None,
            'audio': self.audio is not None,
            'action': True,  # PyAutoGUI toujours disponible
            'meta_learning': {
                'strategies': len(self.learning_state['meta_learning']['strategies']),
                'performance': self.learning_state['meta_learning']['performance']
            },
            'few_shot': {
                'examples': len(self.learning_state['few_shot']['examples']),
                'success_rate': self.learning_state['few_shot']['success_rate']
            },
            'contextual': {
                'contexts': len(self.learning_state['contextual']['contexts']),
                'adaptations': len(self.learning_state['contextual']['adaptations'])
            },
            'memory': {
                'vector_store_size': self.vector_store.ntotal if self.vector_store else 0
            }
        }
