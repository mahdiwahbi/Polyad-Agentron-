#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import time
import unittest
from unittest import IsolatedAsyncioTestCase

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from async_tools import AsyncTools, RetryPolicy, async_function

def slow_function(duration, return_value=None, raise_error=False):
    """Fonction de test qui prend du temps à s'exécuter"""
    time.sleep(duration)
    if raise_error:
        raise ValueError("Erreur de test")
    return return_value or duration

class TestAsyncTools(IsolatedAsyncioTestCase):
    """Tests pour la classe AsyncTools"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.async_tools = AsyncTools(max_workers=4, default_timeout=5.0)
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.async_tools.shutdown()
        
    async def test_run_async(self):
        """Test de la méthode run_async"""
        # Test avec une fonction simple
        result = await self.async_tools.run_async(slow_function, 0.1, "test_value")
        self.assertEqual(result, "test_value")
        
        # Test avec timeout
        with self.assertRaises(asyncio.TimeoutError):
            await self.async_tools.run_async(slow_function, 2.0, timeout=0.5)
            
        # Test avec une exception
        with self.assertRaises(ValueError):
            await self.async_tools.run_async(slow_function, 0.1, raise_error=True)
            
    async def test_parallel_tasks(self):
        """Test de la méthode parallel_tasks"""
        tasks = [
            {'func': slow_function, 'args': [0.1, f"task_{i}"]} 
            for i in range(5)
        ]
        
        results = await self.async_tools.parallel_tasks(tasks)
        self.assertEqual(len(results), 5)
        self.assertEqual(results, ["task_0", "task_1", "task_2", "task_3", "task_4"])
        
        # Test avec une tâche qui échoue
        tasks.append({'func': slow_function, 'args': [0.1], 'kwargs': {'raise_error': True}})
        results = await self.async_tools.parallel_tasks(tasks)
        self.assertEqual(len(results), 6)
        self.assertIsInstance(results[5], dict)
        self.assertFalse(results[5]["success"])
        
    async def test_with_retry(self):
        """Test de la méthode with_retry"""
        # Compteur pour suivre le nombre d'appels
        call_count = [0]
        
        # Fonction qui échoue les N premières fois
        def fail_n_times(n):
            def _func():
                call_count[0] += 1
                if call_count[0] <= n:
                    raise ValueError(f"Échec {call_count[0]}/{n}")
                return "success"
            return _func
        
        # Test avec 2 échecs puis succès
        policy = RetryPolicy(max_retries=3, delay_seconds=0.1)
        result = await self.async_tools.with_retry(fail_n_times(2), retry_policy=policy)
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)  # 2 échecs + 1 succès
        
        # Test avec trop d'échecs
        call_count[0] = 0
        with self.assertRaises(ValueError):
            await self.async_tools.with_retry(fail_n_times(5), retry_policy=policy)
        self.assertEqual(call_count[0], 4)  # 3 échecs + 1 dernier essai
        
    async def test_map_async(self):
        """Test de la méthode map_async"""
        items = list(range(10))
        
        # Fonction qui double la valeur
        def double(x):
            time.sleep(0.1)  # Simuler un traitement
            return x * 2
            
        results = await self.async_tools.map_async(double, items, max_concurrency=3)
        self.assertEqual(results, [0, 2, 4, 6, 8, 10, 12, 14, 16, 18])
        
    async def test_get_stats(self):
        """Test de la méthode get_stats"""
        # Exécuter quelques tâches
        for i in range(5):
            await self.async_tools.run_async(slow_function, 0.1)
            
        # Exécuter une tâche qui échoue
        with self.assertRaises(ValueError):
            await self.async_tools.run_async(slow_function, 0.1, raise_error=True)
            
        # Vérifier les statistiques
        stats = self.async_tools.get_stats()
        self.assertEqual(stats["tasks_completed"], 5)
        self.assertEqual(stats["tasks_failed"], 1)
        self.assertGreater(stats["avg_completion_time"], 0)
        self.assertEqual(stats["active_tasks"], 0)
        self.assertAlmostEqual(stats["success_rate"], 5/6)
        
    async def test_async_function_decorator(self):
        """Test du décorateur async_function"""
        @async_function
        def sync_function(x, y):
            time.sleep(0.1)
            return x + y
            
        result = await sync_function(5, 7)
        self.assertEqual(result, 12)

if __name__ == '__main__':
    unittest.main()
