#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import psutil
import threading
from typing import Dict, Any

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules Polyad
from resource_manager import ResourceManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def simulate_load(duration: int = 10, cpu_intensive: bool = True, memory_intensive: bool = False):
    """
    Simule une charge sur le système
    
    Args:
        duration: Durée de la simulation en secondes
        cpu_intensive: Si True, génère une charge CPU
        memory_intensive: Si True, génère une charge mémoire
    """
    print(f"Simulation de charge pendant {duration} secondes...")
    
    # Allouer de la mémoire si demandé
    memory_blocks = []
    if memory_intensive:
        print("Allocation de mémoire...")
        try:
            # Allouer progressivement jusqu'à 500MB
            for _ in range(50):
                # Allouer ~10MB à chaque itération
                memory_blocks.append(bytearray(10 * 1024 * 1024))
                time.sleep(0.1)
        except MemoryError:
            print("Limite de mémoire atteinte!")
    
    # Simuler une charge CPU si demandé
    start_time = time.time()
    if cpu_intensive:
        print("Génération de charge CPU...")
        end_time = start_time + duration
        
        # Boucle de calcul intensif
        while time.time() < end_time:
            # Calcul intensif
            for _ in range(10000000):
                x = 1.0001 ** 10000
                if time.time() >= end_time:
                    break
    else:
        # Simplement attendre
        time.sleep(duration)
    
    # Libérer la mémoire
    if memory_intensive:
        print("Libération de la mémoire...")
        memory_blocks.clear()
    
    print(f"Simulation terminée. Durée: {time.time() - start_time:.2f}s")

def monitor_resources(resource_manager: ResourceManager, interval: float = 1.0, duration: int = 15):
    """
    Surveille les ressources système pendant une durée spécifiée
    
    Args:
        resource_manager: Instance du gestionnaire de ressources
        interval: Intervalle entre les vérifications en secondes
        duration: Durée totale de la surveillance en secondes
    """
    iterations = int(duration / interval)
    
    print(f"Démarrage de la surveillance des ressources (intervalle: {interval}s, durée: {duration}s)...")
    
    for i in range(iterations):
        # Obtenir les statistiques actuelles
        stats = resource_manager.get_stats()
        current = stats.get("current", {})
        
        # Afficher les informations
        print(f"[{i+1}/{iterations}] Ressources:")
        print(f"  CPU: {current.get('cpu_percent', 0):.1f}%")
        print(f"  RAM utilisée: {current.get('ram_used_gb', 0):.2f} GB")
        print(f"  RAM disponible: {current.get('ram_available_gb', 0):.2f} GB")
        print(f"  Température: {current.get('temperature', 0):.1f}°C")
        
        # Vérifier si les ressources sont suffisantes
        resources_ok = resource_manager.check_resources()
        print(f"  Ressources suffisantes: {'Oui' if resources_ok else 'Non'}")
        
        # Attendre avant la prochaine itération
        if i < iterations - 1:
            time.sleep(interval)
    
    print("Surveillance terminée.")

def main():
    """Fonction principale de démonstration"""
    print("Démarrage de la démonstration du gestionnaire de ressources...")
    
    # Créer une instance du gestionnaire de ressources
    resource_manager = ResourceManager()
    
    try:
        # 1. Afficher les informations système
        print("\n1. Informations système:")
        system_info = resource_manager.get_system_info()
        
        print(f"  Système d'exploitation: {system_info.get('os', 'Inconnu')}")
        print(f"  Version: {system_info.get('os_version', 'Inconnue')}")
        print(f"  Processeur: {system_info.get('cpu_model', 'Inconnu')}")
        print(f"  Cœurs physiques: {system_info.get('physical_cores', 0)}")
        print(f"  Cœurs logiques: {system_info.get('logical_cores', 0)}")
        print(f"  RAM totale: {system_info.get('total_ram_gb', 0):.2f} GB")
        
        # 2. Vérifier les ressources actuelles
        print("\n2. Ressources actuelles:")
        stats = resource_manager.get_stats()
        current = stats.get("current", {})
        
        print(f"  CPU: {current.get('cpu_percent', 0):.1f}%")
        print(f"  RAM utilisée: {current.get('ram_used_gb', 0):.2f} GB")
        print(f"  RAM disponible: {current.get('ram_available_gb', 0):.2f} GB")
        print(f"  Température: {current.get('temperature', 0):.1f}°C")
        
        # 3. Vérifier si les ressources sont suffisantes
        print("\n3. Vérification des ressources:")
        resources_ok = resource_manager.check_resources()
        print(f"  Ressources suffisantes: {'Oui' if resources_ok else 'Non'}")
        
        # 4. Simuler une charge et surveiller les ressources
        print("\n4. Simulation de charge et surveillance:")
        
        # Démarrer la surveillance dans un thread séparé
        monitor_thread = threading.Thread(
            target=monitor_resources,
            args=(resource_manager, 1.0, 12)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Attendre un peu pour que la surveillance démarre
        time.sleep(1)
        
        # Simuler une charge CPU
        simulate_load(duration=10, cpu_intensive=True, memory_intensive=False)
        
        # Attendre que la surveillance se termine
        monitor_thread.join()
        
        # 5. Obtenir le modèle optimal
        print("\n5. Sélection du modèle optimal:")
        optimal_model = resource_manager.get_optimal_model()
        print(f"  Modèle recommandé: {optimal_model}")
        
        # 6. Afficher les métriques collectées
        print("\n6. Métriques collectées:")
        metrics = resource_manager.get_metrics()
        
        print(f"  Nombre de métriques: {len(metrics)}")
        if metrics:
            last_metric = metrics[-1]
            print(f"  Dernière métrique:")
            print(f"    Timestamp: {last_metric.get('timestamp', 0)}")
            print(f"    CPU: {last_metric.get('cpu_percent', 0):.1f}%")
            print(f"    RAM: {last_metric.get('ram_used_gb', 0):.2f} GB")
            print(f"    Température: {last_metric.get('temperature', 0):.1f}°C")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    print("\nDémonstration terminée.")

if __name__ == "__main__":
    main()
