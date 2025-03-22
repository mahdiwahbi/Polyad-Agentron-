import asyncio
import logging
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import List, Dict, Any, Callable, Coroutine, Optional, Union

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'async_tools.log')),
        logging.StreamHandler()
    ]
)

class RetryPolicy:
    """Politique de réessai pour les opérations asynchrones"""
    def __init__(self, max_retries: int = 3, delay_seconds: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.backoff_factor = backoff_factor

class AsyncTools:
    def __init__(self, max_workers: int = 6, default_timeout: float = 30.0):
        """
        Initialise les outils asynchrones
        
        Args:
            max_workers: Nombre maximum de workers dans le pool
            default_timeout: Délai d'expiration par défaut en secondes
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()
        self.default_timeout = default_timeout
        self.max_workers = max_workers
        self.active_tasks = 0
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_completion_time": 0,
            "total_completion_time": 0
        }
        
        logging.info(f"AsyncTools initialisé avec {max_workers} workers")
        
    async def run_async(self, func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
        """
        Exécute une fonction de manière asynchrone
        
        Args:
            func: Fonction à exécuter
            *args: Arguments positionnels
            timeout: Délai d'expiration en secondes (None = utiliser la valeur par défaut)
            **kwargs: Arguments nommés
            
        Returns:
            Any: Résultat de la fonction
            
        Raises:
            asyncio.TimeoutError: Si l'exécution dépasse le délai d'expiration
            Exception: Toute exception levée par la fonction
        """
        start_time = time.time()
        self.active_tasks += 1
        
        timeout_value = timeout if timeout is not None else self.default_timeout
        
        try:
            logging.debug(f"Démarrage tâche asynchrone: {func.__name__}")
            
            # Exécuter la fonction dans le pool de threads avec timeout
            result = await asyncio.wait_for(
                self.loop.run_in_executor(
                    self.executor,
                    partial(func, *args, **kwargs)
                ),
                timeout=timeout_value
            )
            
            # Mettre à jour les statistiques
            self.stats["tasks_completed"] += 1
            elapsed = time.time() - start_time
            self.stats["total_completion_time"] += elapsed
            self.stats["avg_completion_time"] = (
                self.stats["total_completion_time"] / self.stats["tasks_completed"]
            )
            
            logging.debug(f"Tâche terminée: {func.__name__} en {elapsed:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            self.stats["tasks_failed"] += 1
            logging.error(f"Délai d'expiration pour {func.__name__} après {timeout_value}s")
            raise
        except Exception as e:
            self.stats["tasks_failed"] += 1
            logging.error(f"Erreur dans {func.__name__}: {e}\n{traceback.format_exc()}")
            raise
        finally:
            self.active_tasks -= 1
        
    async def parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """
        Exécute plusieurs tâches en parallèle
        
        Args:
            tasks: Liste de tâches à exécuter, chaque tâche étant un dictionnaire avec:
                - 'func': Fonction à exécuter
                - 'args': Liste d'arguments (optionnel)
                - 'kwargs': Dictionnaire d'arguments nommés (optionnel)
                - 'timeout': Délai d'expiration en secondes (optionnel)
                
        Returns:
            List[Any]: Liste des résultats dans le même ordre que les tâches
        """
        if not tasks:
            return []
            
        logging.info(f"Exécution de {len(tasks)} tâches en parallèle")
        
        # Préparer les coroutines
        coroutines = []
        for task in tasks:
            func = task['func']
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})
            timeout = task.get('timeout', self.default_timeout)
            
            coroutines.append(self.run_async(func, *args, timeout=timeout, **kwargs))
            
        # Exécuter toutes les tâches en parallèle
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Traiter les résultats
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Tâche {i} a échoué: {result}")
                task_name = tasks[i]['func'].__name__ if hasattr(tasks[i]['func'], '__name__') else str(tasks[i]['func'])
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "task": task_name
                })
            else:
                processed_results.append(result)
                
        return processed_results
    
    async def with_retry(self, func: Callable, *args, 
                        retry_policy: Optional[RetryPolicy] = None, 
                        **kwargs) -> Any:
        """
        Exécute une fonction avec politique de réessai
        
        Args:
            func: Fonction à exécuter
            *args: Arguments positionnels
            retry_policy: Politique de réessai (None = politique par défaut)
            **kwargs: Arguments nommés
            
        Returns:
            Any: Résultat de la fonction
            
        Raises:
            Exception: Si tous les essais échouent
        """
        # Utiliser la politique par défaut si non spécifiée
        policy = retry_policy or RetryPolicy()
        
        # Tentatives
        for attempt in range(policy.max_retries + 1):
            try:
                if attempt > 0:
                    logging.info(f"Tentative {attempt}/{policy.max_retries} pour {func.__name__}")
                    
                return await self.run_async(func, *args, **kwargs)
                
            except Exception as e:
                if attempt >= policy.max_retries:
                    logging.error(f"Échec après {attempt+1} tentatives: {e}")
                    raise
                    
                # Calculer le délai avant la prochaine tentative
                delay = policy.delay_seconds * (policy.backoff_factor ** attempt)
                logging.warning(f"Erreur dans {func.__name__}, nouvel essai dans {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
    
    async def map_async(self, func: Callable, items: List[Any], 
                      max_concurrency: Optional[int] = None) -> List[Any]:
        """
        Applique une fonction à chaque élément d'une liste de manière asynchrone
        
        Args:
            func: Fonction à appliquer
            items: Liste d'éléments
            max_concurrency: Nombre maximum de tâches concurrentes (None = utiliser max_workers)
            
        Returns:
            List[Any]: Liste des résultats
        """
        if not items:
            return []
            
        # Limiter la concurrence
        concurrency = min(
            max_concurrency or self.max_workers,
            self.max_workers,
            len(items)
        )
        
        logging.info(f"Map asynchrone sur {len(items)} éléments avec concurrence de {concurrency}")
        
        # Créer un sémaphore pour limiter la concurrence
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_item(item):
            async with semaphore:
                return await self.run_async(func, item)
                
        # Créer les tâches
        tasks = [process_item(item) for item in items]
        
        # Exécuter toutes les tâches
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'utilisation
        
        Returns:
            Dict[str, Any]: Statistiques d'utilisation
        """
        return {
            **self.stats,
            "active_tasks": self.active_tasks,
            "success_rate": (
                self.stats["tasks_completed"] / 
                (self.stats["tasks_completed"] + self.stats["tasks_failed"])
                if (self.stats["tasks_completed"] + self.stats["tasks_failed"]) > 0 
                else 1.0
            )
        }
    
    def shutdown(self, wait: bool = True):
        """
        Arrête proprement l'exécuteur
        
        Args:
            wait: Attendre la fin des tâches en cours
        """
        logging.info(f"Arrêt de AsyncTools (wait={wait})")
        self.executor.shutdown(wait=wait)


# Décorateur pour transformer une fonction synchrone en asynchrone
def async_function(func):
    """
    Décorateur pour transformer une fonction synchrone en asynchrone
    
    Usage:
        @async_function
        def ma_fonction(arg1, arg2):
            return arg1 + arg2
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))
    return wrapper
