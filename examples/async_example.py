#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import asyncio
import random
import logging
from typing import Dict, Any, List

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules Polyad
from async_tools import AsyncTools, RetryPolicy, async_function

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Simuler des tâches avec différents comportements
async def task_success(task_id: int, duration: float = 1.0) -> Dict[str, Any]:
    """Tâche qui réussit toujours"""
    await asyncio.sleep(duration)
    return {
        "task_id": task_id,
        "status": "success",
        "result": f"Résultat de la tâche {task_id}",
        "duration": duration
    }

async def task_random_failure(task_id: int, failure_rate: float = 0.5) -> Dict[str, Any]:
    """Tâche qui échoue aléatoirement"""
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    if random.random() < failure_rate:
        raise RuntimeError(f"Échec aléatoire de la tâche {task_id}")
    
    return {
        "task_id": task_id,
        "status": "success",
        "result": f"Résultat de la tâche {task_id} (après échec potentiel)"
    }

async def task_timeout(task_id: int, duration: float = 5.0) -> Dict[str, Any]:
    """Tâche qui prend beaucoup de temps (potentiel timeout)"""
    await asyncio.sleep(duration)
    return {
        "task_id": task_id,
        "status": "success",
        "result": f"Résultat de la tâche longue {task_id}",
        "duration": duration
    }

def format_duration(seconds: float) -> str:
    """Formate la durée en secondes"""
    return f"{seconds:.2f}s"

async def main_async():
    """Fonction principale asynchrone"""
    print("Démarrage de la démonstration des outils asynchrones...")
    
    # Créer une instance d'AsyncTools
    async_tools = AsyncTools(
        max_workers=4,
        default_timeout=3.0
    )
    
    # Configurer une politique de réessai
    retry_policy = RetryPolicy(
        max_retries=3,
        delay_seconds=0.5,
        backoff_factor=2.0
    )
    
    try:
        # 1. Exécuter des tâches simples en parallèle
        print("\n1. Exécution de tâches simples en parallèle:")
        tasks = [
            {"func": task_success, "args": [i], "kwargs": {"duration": 0.5 + i * 0.2}}
            for i in range(5)
        ]
        
        start_time = time.time()
        results = await async_tools.parallel_tasks(tasks)
        elapsed = time.time() - start_time
        
        print(f"  Temps total: {format_duration(elapsed)}")
        print(f"  Temps séquentiel estimé: {format_duration(sum(r['duration'] for r in results))}")
        print(f"  Accélération: {sum(r['duration'] for r in results) / elapsed:.2f}x")
        
        # 2. Exécuter des tâches avec échecs aléatoires et réessais
        print("\n2. Exécution de tâches avec échecs aléatoires et réessais:")
        tasks_with_failures = [
            {
                "func": task_random_failure, 
                "args": [i], 
                "kwargs": {"failure_rate": 0.7},
                "retry_policy": retry_policy
            }
            for i in range(5)
        ]
        
        start_time = time.time()
        results = await async_tools.parallel_tasks(tasks_with_failures)
        elapsed = time.time() - start_time
        
        print(f"  Temps total: {format_duration(elapsed)}")
        
        # Analyser les résultats
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        failure_count = len(results) - success_count
        
        print(f"  Tâches réussies: {success_count}/{len(results)}")
        print(f"  Tâches échouées: {failure_count}/{len(results)}")
        
        # 3. Exécuter des tâches avec timeout
        print("\n3. Exécution de tâches avec timeout:")
        timeout_tasks = [
            {
                "func": task_timeout, 
                "args": [i], 
                "kwargs": {"duration": 2.0 if i % 2 == 0 else 4.0},
                "timeout": 3.0  # Timeout de 3 secondes
            }
            for i in range(4)
        ]
        
        start_time = time.time()
        results = await async_tools.parallel_tasks(timeout_tasks)
        elapsed = time.time() - start_time
        
        print(f"  Temps total: {format_duration(elapsed)}")
        
        # Analyser les résultats
        timeout_count = sum(1 for r in results if isinstance(r, Exception) and "timeout" in str(r).lower())
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        
        print(f"  Tâches réussies: {success_count}/{len(results)}")
        print(f"  Tâches timeout: {timeout_count}/{len(results)}")
        
        # 4. Statistiques
        print("\n4. Statistiques d'exécution:")
        stats = async_tools.get_stats()
        
        print(f"  Tâches complétées: {stats.get('tasks_completed', 0)}")
        print(f"  Tâches échouées: {stats.get('tasks_failed', 0)}")
        print(f"  Tâches timeout: {stats.get('tasks_timeout', 0)}")
        print(f"  Temps moyen par tâche: {stats.get('avg_task_time', 0):.2f}s")
        print(f"  Réessais effectués: {stats.get('retries', 0)}")
        
    finally:
        # Arrêter AsyncTools proprement
        await async_tools.shutdown(wait=True)
        print("\nDémonstration terminée.")

def main():
    """Point d'entrée principal"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
