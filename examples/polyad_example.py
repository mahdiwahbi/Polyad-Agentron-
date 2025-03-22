#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules Polyad
from polyad import Polyad

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_temp_config():
    """Crée un fichier de configuration temporaire pour l'exemple"""
    config = {
        "temperature": 0.7,
        "max_memory_tokens": 300,
        "parallel_iterations": 3,
        "enable_fallback": True,
        "max_retries": 2,
        "retry_delay": 1.0,
        "backoff_factor": 2.0,
        "default_timeout": 15.0,
        "refinement_timeout": 10.0,
        "cache_ttl": 3600,
        "log_level": "INFO",
        "resource_limits": {
            "max_cpu_percent": 90,
            "min_ram_available_gb": 1.0,
            "max_temperature": 85
        },
        "models": {
            "default": "gemma3:12b-q2_K",
            "fallback": "gemma3:2b-q2_K"
        }
    }
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_path

def format_time(seconds: float) -> str:
    """Formate le temps en secondes"""
    return f"{seconds:.2f}s"

def main():
    """Fonction principale de démonstration"""
    print("Démarrage de la démonstration de Polyad...")
    
    # Créer une configuration temporaire
    config_path = create_temp_config()
    
    # Initialiser Polyad
    polyad = Polyad(config_path=config_path)
    
    try:
        # 1. Requête simple
        print("\n1. Requête simple:")
        start_time = time.time()
        result = polyad.run("Explique brièvement ce qu'est l'intelligence artificielle")
        elapsed = time.time() - start_time
        
        print(f"  Temps d'exécution: {format_time(elapsed)}")
        print(f"  Résultat: {result[:150]}...")
        
        # 2. Traitement par lots
        print("\n2. Traitement par lots:")
        batch = [
            "Qu'est-ce que le machine learning?",
            "Quelles sont les applications de l'IA dans la santé?",
            "Comment fonctionne le deep learning?"
        ]
        
        print(f"  Exécution de {len(batch)} tâches en parallèle")
        start_time = time.time()
        
        # Utiliser asyncio pour exécuter le traitement par lots
        import asyncio
        results = asyncio.run(polyad.process_batch(batch))
        
        elapsed = time.time() - start_time
        avg_time = elapsed / len(batch)
        
        print(f"  Temps d'exécution total: {format_time(elapsed)}")
        print(f"  Temps moyen par requête: {format_time(avg_time)}")
        
        for i, result in enumerate(results):
            if isinstance(result, dict) and "error" in result:
                print(f"  Requête {i+1}: Échec - {result['error']}")
            elif isinstance(result, Exception):
                print(f"  Requête {i+1}: Échec - {str(result)}")
            else:
                print(f"  Requête {i+1}: {str(result)[:50]}...")
        
        # 3. Statistiques de performance
        print("\nStatistiques de performance:")
        try:
            stats = polyad.get_stats()
            
            # Afficher les statistiques de ressources
            resource_stats = stats.get("resource_stats", {}).get("current", {})
            print(f"  CPU: {resource_stats.get('cpu_percent', 0):.1f}%")
            print(f"  RAM disponible: {resource_stats.get('ram_available_gb', 0):.2f} GB")
            print(f"  Température: {resource_stats.get('temperature', 0):.1f}°C")
            
            # Afficher les statistiques d'outils
            tools_stats = stats.get("tools_stats", {})
            print(f"  Recherches web: {tools_stats.get('web_searches', 0)}")
            print(f"  Ratio de cache: {tools_stats.get('cache_hit_ratio', 0):.2f}")
            
            # Afficher les statistiques asynchrones
            async_stats = stats.get("async_stats", {})
            print(f"  Tâches asynchrones: {async_stats.get('tasks_completed', 0)}")
            print(f"  Temps moyen des tâches: {async_stats.get('avg_task_time', 0):.2f}s")
            
        except Exception as e:
            print(f"  Erreur lors de la récupération des statistiques: {e}")
    
    finally:
        # Nettoyer les ressources
        try:
            polyad.cleanup()
        except Exception as e:
            print(f"  Erreur lors du nettoyage: {e}")
        
        # Supprimer le fichier de configuration temporaire
        try:
            os.remove(config_path)
        except:
            pass

if __name__ == "__main__":
    main()
