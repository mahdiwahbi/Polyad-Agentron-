#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import platform
import subprocess
from typing import Dict, List, Optional, Tuple

def check_dependencies() -> List[str]:
    """
    Vérifie les dépendances requises
    
    Returns:
        List[str]: Dépendances manquantes
    """
    # Dépendances requises
    dependencies = [
        "langchain",
        "langchain-community",
        "langchain-core",
        "langchain-ollama",
        "ollama",
        "psutil",
        "opencv-python",
        "SpeechRecognition",
        "pyautogui",
        "duckduckgo-search",
        "faiss-cpu",
        "pyaudio",
        "numpy",
        "Pillow",
        "requests",
        "python-dotenv",
        "asyncio",
        "aiohttp",
        "aiosqlite",
        "fastapi",
        "uvicorn",
        "pydantic",
        "matplotlib",
        "pandas",
        "scikit-learn",
        "rich",
        "typer",
        "scipy"
    ]
    
    # Fichiers requis
    required_files = [
        "polyad.py",
        "requirements.txt",
        "README.md",
        "utils/logger.py",
        "utils/monitoring.py",
        "utils/tools.py",
        "utils/async_tools.py"
    ]
    
    # Dossiers requis
    required_dirs = [
        "utils",
        "dashboard",
        "models",
        "cache",
        "logs"
    ]
    
    missing = []
    
    # Vérifie la version de Python
    if sys.version_info < (3, 8):
        missing.append("Python >= 3.8")
    
    # Vérifie les dépendances
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing.extend([dep for dep in dependencies if dep.lower() not in installed])
    except Exception as e:
        print(f"Erreur lors de la vérification des dépendances : {e}")
        missing.extend(dependencies)
    
    # Vérifie les fichiers
    missing.extend([f for f in required_files if not os.path.exists(f)])
    
    # Vérifie les dossiers
    missing.extend([d for d in required_dirs if not os.path.exists(d)])
    
    return missing

def get_cpu_info() -> Dict[str, str]:
    """
    Récupère les informations sur le processeur
    
    Returns:
        Dict[str, str]: Informations sur le processeur
    """
    info = {}
    
    try:
        if platform.system() == "Darwin":  # macOS
            output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode()
            info["model"] = output.strip()
            
            output = subprocess.check_output(["sysctl", "-n", "hw.ncpu"]).decode()
            info["cores"] = output.strip()
            
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        info["model"] = line.split(":")[1].strip()
                        break
                        
            info["cores"] = str(os.cpu_count())
            
        else:  # Windows ou autre
            info["model"] = platform.processor()
            info["cores"] = str(os.cpu_count())
            
    except Exception as e:
        print(f"Erreur lors de la récupération des informations sur le processeur : {e}")
        info["model"] = "Inconnu"
        info["cores"] = "Inconnu"
        
    return info

def check_config() -> Tuple[bool, str]:
    """
    Vérifie le fichier de configuration
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    # Vérifie si l'exemple existe
    if not os.path.exists("config.json.example"):
        return False, "config.json.example non trouvé"
        
    try:
        # Charge l'exemple de configuration
        with open("config.json.example") as f:
            example_config = json.load(f)
            
        # Vérifie les clés requises
        required_keys = [
            "temperature",
            "max_memory_tokens",
            "parallel_iterations",
            "enable_fallback",
            "max_retries",
            "retry_delay",
            "default_timeout"
        ]
        
        missing_keys = [key for key in required_keys if key not in example_config]
        
        if missing_keys:
            return False, f"Clés requises manquantes dans la configuration : {', '.join(missing_keys)}"
            
        return True, "Fichier de configuration valide"
        
    except json.JSONDecodeError:
        return False, "JSON invalide dans config.json.example"
    except Exception as e:
        return False, f"Erreur lors de la vérification de la configuration : {e}"

def check_ollama() -> Tuple[bool, str]:
    """
    Vérifie l'installation d'Ollama
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    try:
        # Vérifie si la commande ollama existe
        if subprocess.run(["which", "ollama"], capture_output=True).returncode != 0:
            return False, "Ollama non trouvé dans le PATH"
            
        # Vérifie la version d'Ollama
        version = subprocess.check_output(["ollama", "version"]).decode().strip()
        
        # Vérifie les modèles disponibles
        models = subprocess.check_output(["ollama", "list"]).decode().strip()
        
        if not models:
            return False, "Aucun modèle Ollama trouvé"
            
        return True, f"Ollama {version} installé avec les modèles : {models}"
        
    except Exception as e:
        return False, f"Erreur lors de la vérification d'Ollama : {e}"

def check_gpu() -> Tuple[bool, str]:
    """
    Vérifie la disponibilité de la carte graphique
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    try:
        if platform.system() == "Darwin":  # macOS
            # Vérifie la prise en charge de Metal
            output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode()
            if "Metal" in output:
                return True, "Prise en charge de Metal pour la carte graphique disponible"
                
        elif platform.system() == "Linux":
            # Vérifie la présence d'une carte graphique NVIDIA
            nvidia_smi = subprocess.run(["nvidia-smi"], capture_output=True)
            if nvidia_smi.returncode == 0:
                return True, "Carte graphique NVIDIA disponible"
                
        return False, "Aucune carte graphique compatible trouvée"
        
    except Exception as e:
        return False, f"Erreur lors de la vérification de la carte graphique : {e}"

def main():
    """Point d'entrée principal"""
    print("\n=== Vérification de l'installation de Polyad ===\n")
    
    # Vérifie les informations système
    print("Informations système :")
    print(f"Système d'exploitation : {platform.system()} {platform.release()}")
    print(f"Python : {platform.python_version()}")
    
    cpu_info = get_cpu_info()
    print(f"Processeur : {cpu_info['model']} ({cpu_info['cores']} cœurs)")
    
    # Vérifie les dépendances
    print("\nVérification des dépendances...")
    missing = check_dependencies()
    if missing:
        print("Dépendances manquantes :")
        for item in missing:
            print(f"  - {item}")
    else:
        print("Toutes les dépendances sont installées")
    
    # Vérifie les fichiers
    print("\nVérification des fichiers...")
    success, message = check_config()
    print(f"Configuration : {message}")
    
    # Vérifie Ollama
    print("\nVérification d'Ollama...")
    success, message = check_ollama()
    print(f"Ollama : {message}")
    
    # Vérifie la carte graphique
    print("\nVérification de la carte graphique...")
    success, message = check_gpu()
    print(f"Carte graphique : {message}")
    
    # Affiche le résumé
    print("\n=== Résumé ===")
    if missing:
        print("❌ Certains composants sont manquants")
        sys.exit(1)
    else:
        print("✅ Toutes les vérifications ont réussi")
        sys.exit(0)

if __name__ == "__main__":
    main()
