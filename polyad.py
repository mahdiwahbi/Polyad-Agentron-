import os
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from core.cache.cache_manager import CacheManager
from core.tools.polyad_tools import PolyadTools
from core.tools.async_tools import AsyncTools
from resource_manager import ResourceManager
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import time
import json
import argparse
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable
import traceback
import yaml
import psutil
import subprocess

class PolyadAgent:
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialise l'agent Polyad"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration du logger
        self.logger.setLevel(config['polyad'].get('log_level', 'INFO'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler fichier
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, 'polyad.log'))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info("Initialisation de Polyad...")
        
        # Initialiser le cache
        self.cache = CacheManager(config['cache'])
        
        # Initialiser les outils
        self.tools = PolyadTools(config)
        
        # Initialiser les ressources asynchrones
        self.async_tools = AsyncTools(config)
        
        # Initialiser le modèle
        self.logger.info("Initialisation du modèle...")
        self.llm = Ollama(
            model=self._select_model(),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_memory_tokens', 300)
        )
        
        # Initialiser la mémoire
        self.memory = ConversationBufferMemory()
        
        # Initialiser le gestionnaire de ressources
        self.resource_manager = ResourceManager(config)
        
        # Initialiser le système de surveillance
        self.monitor = SystemMonitor(config)
        
        self.logger.info("Polyad initialisé avec succès")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Charge la configuration depuis un fichier YAML ou utilise les valeurs par défaut"""
        default_config = {
            "polyad": {
                "debug": True,
                "log_level": "DEBUG",
                "environment": "development"
            },
            "cache": {
                "size": 1024 * 1024 * 1024,  # 1GB
                "ttl": 3600,                  # 1 heure
                "cleanup_interval": 300,      # 5 minutes
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 0
                }
            },
            "gpu": {
                "memory_threshold": 0.8,
                "temperature_threshold": 80,
                "optimization_interval": 60  # secondes
            },
            "security": {
                "encryption_key": None,
                "salt": None,
                "iterations": 100000
            },
            "monitoring": {
                "grafana": {
                    "api_key": None,
                    "host": "localhost",
                    "port": 3000
                },
                "metrics_interval": 1,
                "alert_thresholds": {
                    "cpu": 90,
                    "memory": 90,
                    "temperature": 80
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": True,
                "reload": True,
                "workers": 1
            },
            "temperature": 0.7,
            "max_memory_tokens": 300,
            "parallel_iterations": 6,
            "enable_fallback": True,
            "max_retries": 3,
            "retry_delay": 1.0,
            "backoff_factor": 2.0,
            "default_timeout": 30.0
        }
        
        if config_path and isinstance(config_path, str) and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                # Fusionner avec la config par défaut
                default_config.update(user_config)
                logging.info(f"Configuration chargée depuis {config_path}")
            except Exception as e:
                logging.error(f"Erreur lors du chargement de la configuration: {e}")
                
        return default_config

    def _select_model(self) -> str:
        """Sélectionne le modèle optimal"""
        # Vérifier les ressources disponibles
        ram = psutil.virtual_memory().available / (1024 ** 3)
        if ram < 6:
            return "gemma3:12b-q2_K"  # 6-8GB RAM
        else:
            return "gemma3:12b-q4_K_M"  # 8-10GB RAM

    async def process_task(self, task: str) -> str:
        """Traite une tâche avec gestion des ressources"""
        # Vérifier les ressources avant le traitement
        if not await self.monitor.check_resources():
            return "Ressources insuffisantes. Veuillez libérer de la mémoire ou augmenter la RAM."
        
        try:
            # Traiter la tâche
            result = await self.tools.process(task)
            
            # Mettre en cache le résultat
            await self.cache.set(task, result)
            
            return result
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de la tâche: {e}")
            return f"Erreur: {str(e)}"

    async def cleanup(self) -> None:
        """Nettoie les ressources utilisées par l'agent"""
        try:
            # Fermer le cache
            if hasattr(self, 'cache') and self.cache:
                self.logger.info("Nettoyage du cache...")
                await self.cache.cleanup()
                await self.cache.close()
            
            # Fermer les outils
            if hasattr(self, 'tools') and self.tools:
                self.logger.info("Nettoyage des outils...")
                await self.tools.cleanup()
            
            # Fermer les ressources asynchrones
            if hasattr(self, 'async_tools') and self.async_tools:
                self.logger.info("Nettoyage des ressources asynchrones...")
                await self.async_tools.cleanup()
            
            # Fermer le moniteur
            if hasattr(self, 'monitor') and self.monitor:
                self.logger.info("Arrêt du moniteur...")
                await self.monitor.stop()
            
            self.logger.info("Nettoyage terminé")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage: {e}")
            raise

    async def monitor_resources(self):
        """Surveille les ressources système"""
        while True:
            try:
                # Vérifier CPU
                cpu = psutil.cpu_percent(interval=1)
                if cpu > self.config['monitoring']['alert_thresholds']['cpu']:
                    self.logger.warning(f"CPU usage high: {cpu}%")
                    
                # Vérifier RAM
                ram = psutil.virtual_memory().available / (1024 ** 3)
                if ram < 1:
                    self.logger.warning(f"Low RAM: {ram}GB available")
                    
                # Vérifier température
                temp = self.get_temperature()
                if temp > self.config['monitoring']['alert_thresholds']['temperature']:
                    self.logger.warning(f"High temperature: {temp}°C")
                    
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.config['monitoring']['metrics_interval'])
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance des ressources: {e}")
                await asyncio.sleep(5)

    def get_temperature(self) -> float:
        """Récupère la température du système"""
        try:
            result = subprocess.run(['smc', '-k', 'TC0P', '-r'], 
                                  capture_output=True, 
                                  text=True)
            temp = float(result.stdout.split()[2])
            return temp
        except:
            return 80  # Température par défaut si la commande échoue

    async def offload_to_cloud(self, task: str) -> str:
        """Offload une tâche vers le cloud si nécessaire"""
        # Vérifier les ressources locales
        ram = psutil.virtual_memory().available / (1024 ** 3)
        if ram < 4:  # Seuil pour l'offloading
            self.logger.info("Offloading task to cloud due to low RAM")
            # TODO: Implémenter l'offloading vers AWS Lambda ou Heroku
            return "Task offloaded to cloud"
        return "Task processed locally"

def setup_logging(config: Dict[str, Any]) -> None:
    """Configure le logging"""
    logging.basicConfig(
        level=config['polyad'].get('log_level', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'polyad.log')),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Polyad - Agent d\'intelligence artificielle')
    parser.add_argument('--config', type=str, help='Chemin vers le fichier de configuration')
    parser.add_argument('--task', type=str, help='Tâche à exécuter')
    parser.add_argument('--dev', action='store_true', help='Mode de développement')
    args = parser.parse_args()

    # Charger la configuration
    config = PolyadAgent._load_config(args.config)
    
    # Initialiser le logger
    setup_logging(config)
    
    try:
        # Initialiser l'agent
        agent = PolyadAgent(config)
        
        if args.dev:
            # Mode développement
            asyncio.run(agent.monitor_resources())
        else:
            # Mode production
            if args.task:
                result = asyncio.run(agent.process_task(args.task))
                print(f"Résultat: {result}")
            else:
                print("Aucune tâche spécifiée")
                
    except Exception as e:
        logging.error(f"Erreur principale: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
