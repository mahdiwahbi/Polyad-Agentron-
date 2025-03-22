#!/usr/bin/env python3
import os
import sys
import time
import json
import argparse
import asyncio
from typing import Any, Callable, Dict, List, Optional
from utils.logger import logger
from utils.monitoring import monitor
from utils.tools import PolyadTools
from utils.async_tools import AsyncTools

def test_resource_manager():
    """Teste le gestionnaire de ressources"""
    try:
        # Vérifier les informations système
        system_info = monitor.get_system_info()
        assert isinstance(system_info, dict), "Les informations système doivent être un dictionnaire"
        assert "cpu_count" in system_info, "Le nombre de CPU doit être présent"
        
        # Vérifier la collecte de métriques
        metrics = monitor.collect_metrics()
        assert isinstance(metrics, dict), "Les métriques doivent être un dictionnaire"
        assert "cpu" in metrics, "Les métriques CPU doivent être présentes"
        assert "memory" in metrics, "Les métriques mémoire doivent être présentes"
        
        # Vérifier la santé système
        health = monitor.get_system_health()
        assert isinstance(health, dict), "La santé système doit être un dictionnaire"
        assert "cpu" in health, "La santé CPU doit être présente"
        assert "memory" in health, "La santé mémoire doit être présente"
        
        return True, "Test du gestionnaire de ressources réussi"
        
    except Exception as e:
        logger.error(f"Erreur lors du test de Gestionnaire de ressources: {str(e)}")
        raise
        
def test_tools():
    """Teste les outils Polyad"""
    try:
        tools = PolyadTools()
        
        # Tester la génération de texte
        prompt = "Bonjour, comment ça va?"
        result = tools.generate_text(prompt)
        assert isinstance(result, str), "Le résultat doit être une chaîne"
        assert len(result) > 0, "Le résultat ne doit pas être vide"
        
        # Nettoyer
        tools.cleanup()
        
        return True, "Test des outils réussi"
        
    except Exception as e:
        logger.error(f"Erreur lors du test de Outils Polyad: {str(e)}")
        raise
        
async def test_task(x: int) -> int:
    """Tâche de test asynchrone"""
    await asyncio.sleep(0.1)
    return x * 2
    
def test_async_tools():
    """Teste les outils asynchrones"""
    try:
        async_tools = AsyncTools()
        
        # Créer des tâches de test
        tasks = [
            {"func": test_task, "args": [1], "name": "test_task"},
            {"func": test_task, "args": [2], "name": "test_task"},
            {"func": test_task, "args": [3], "name": "test_task"},
            {"func": test_task, "args": [4], "name": "test_task"}
        ]
        
        # Exécuter les tâches
        results = async_tools.run_tasks(tasks)
        
        # Vérifier les résultats
        expected = [2, 4, 6, 8]
        actual = [r["result"] for r in results if r["success"]]
        
        if actual != expected:
            raise ValueError(f"Résultats incorrects: {actual} != {expected}")
            
        # Nettoyer
        async_tools.cleanup()
        
        return True, "Test des outils asynchrones réussi"
        
    except Exception as e:
        logger.error(f"Erreur lors du test de Outils asynchrones: {str(e)}")
        raise
        
def test_polyad():
    """Teste Polyad dans son ensemble"""
    try:
        # Vérifier que les composants principaux sont présents
        components = [
            "polyad.py",
            "requirements.txt",
            "README.md",
            "utils/logger.py",
            "utils/monitoring.py",
            "utils/tools.py",
            "utils/async_tools.py"
        ]
        
        for component in components:
            assert os.path.exists(component), f"Le composant {component} est manquant"
            
        return True, "Test de Polyad réussi"
        
    except Exception as e:
        logger.error(f"Erreur lors du test de Polyad: {str(e)}")
        raise
        
def run_component_test(component: str) -> bool:
    """
    Exécute un test de composant spécifique
    
    Args:
        component: Nom du composant à tester
        
    Returns:
        bool: True si le test a réussi
    """
    test_map = {
        "resource": test_resource_manager,
        "tools": test_tools,
        "async": test_async_tools,
        "polyad": test_polyad
    }
    
    if component not in test_map:
        logger.error(f"Composant inconnu: {component}")
        return False
        
    try:
        test_func = test_map[component]
        result = test_func()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test de {component}: {str(e)}")
        return False
        
def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Tests Polyad")
    parser.add_argument("--component", type=str, choices=["resource", "tools", "async", "polyad"],
                       help="Composant spécifique à tester")
                       
    args = parser.parse_args()
    
    try:
        if args.component:
            success = run_component_test(args.component)
        else:
            # Tester tous les composants
            success = all([
                run_component_test("resource"),
                run_component_test("tools"),
                run_component_test("async"),
                run_component_test("polyad")
            ])
            
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
