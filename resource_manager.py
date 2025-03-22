import psutil
import platform
import subprocess
import os
import json
import time
from typing import Literal, Dict, Any, Optional
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'resource_manager.log')),
        logging.StreamHandler()
    ]
)

class ResourceManager:
    def __init__(self):
        self.min_ram_gb = 1.0
        self.max_cpu_percent = 80
        self.max_temp = 80
        self.using_gpu = self.is_gpu_available()
        self.callback_manager = None  # Sera initialisé plus tard
        self.metrics_history = []
        self.last_optimization_time = time.time()
        self.optimization_interval = 60  # secondes
        
        # Créer le dossier de logs s'il n'existe pas
        os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)
        
        # Désactiver le swap uniquement si nous sommes en mode root
        if os.geteuid() == 0:
            self.disable_swap()
        else:
            logging.warning("Exécution sans privilèges root, impossible de désactiver le swap")
            
        # Initialiser le fichier de métriques
        self.metrics_file = os.path.join(os.path.dirname(__file__), 'logs', 'metrics.json')
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w') as f:
                json.dump([], f)
    
    def get_optimal_model(self) -> str:
        """Sélectionne le modèle optimal en fonction des ressources disponibles"""
        available_ram = psutil.virtual_memory().available / (1024**3)  # GB
        
        # Logging de la décision
        logging.info(f"Sélection du modèle avec {available_ram:.2f} GB RAM disponible")
        
        if available_ram > 10:
            return "gemma3:12b-q4_0"  # Haute qualité
        elif available_ram > 6:
            return "gemma3:12b-q2_K"  # Économe
        else:
            logging.error(f"RAM insuffisante: {available_ram:.2f} GB")
            raise MemoryError(f"RAM insuffisante: {available_ram:.2f} GB disponible, minimum requis: 6 GB")
            
    def is_gpu_available(self) -> bool:
        """Vérifie si le GPU est disponible et utilisable"""
        if platform.system() == "Darwin":
            try:
                # Vérifier si Metal est disponible sur macOS
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"], 
                    capture_output=True, 
                    text=True
                )
                
                # Vérifier si AMD Radeon est mentionné
                has_amd = "AMD Radeon" in result.stdout
                
                logging.info(f"Détection GPU: AMD Radeon {'disponible' if has_amd else 'non détecté'}")
                return has_amd
            except Exception as e:
                logging.error(f"Erreur lors de la détection du GPU: {e}")
                return False
        return False
        
    def get_cpu_temperature(self) -> float:
        """Obtient la température CPU actuelle"""
        if platform.system() == "Darwin":
            try:
                # Utiliser powermetrics pour obtenir la température sur macOS
                cmd = ["sudo", "powermetrics", "--samplers", "smc", "-n1"]
                output = subprocess.check_output(cmd, text=True)
                
                # Extraire la température
                temp_line = [line for line in output.split('\n') if "CPU die temperature" in line]
                if temp_line:
                    temp = float(temp_line[0].split(':')[1].split()[0])
                    logging.debug(f"Température CPU: {temp}°C")
                    return temp
                return 0.0
            except Exception as e:
                logging.error(f"Erreur lors de la lecture de la température: {e}")
                return 0.0
        return 0.0
    
    def should_use_parallel(self) -> bool:
        """Détermine si le traitement parallèle doit être utilisé"""
        resources = self.monitor_resources()
        
        # Décision basée sur les ressources actuelles
        should_parallel = (resources["cpu_percent"] < self.max_cpu_percent and 
                          resources["temperature"] < self.max_temp and
                          resources["ram_available_gb"] > 2.0)
        
        logging.info(f"Décision traitement parallèle: {should_parallel} (CPU: {resources['cpu_percent']}%, Temp: {resources['temperature']}°C)")
        return should_parallel
    
    def disable_swap(self):
        """Désactive le swap pour améliorer les performances"""
        if platform.system() == "Darwin":
            try:
                logging.info("Tentative de désactivation du swap...")
                subprocess.run(["sudo", "launchctl", "unload", "-w", 
                              "/System/Library/LaunchDaemons/com.apple.dynamic_pager.plist"],
                              check=True)
                logging.info("Swap désactivé avec succès")
            except Exception as e:
                logging.error(f"Impossible de désactiver le swap: {e}")
    
    def monitor_resources(self) -> Dict[str, Any]:
        """Surveille et enregistre les ressources système"""
        # Collecter les statistiques
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_available = psutil.virtual_memory().available / (1024**3)
        temperature = self.get_cpu_temperature()
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "ram_available_gb": ram_available,
            "gpu_available": self.using_gpu,
            "temperature": temperature,
            "ram_used_percent": psutil.virtual_memory().percent,
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
        
        # Enregistrer l'historique des métriques
        self.metrics_history.append(stats)
        if len(self.metrics_history) > 100:  # Garder seulement les 100 dernières mesures
            self.metrics_history.pop(0)
            
        # Enregistrer dans le fichier de métriques périodiquement
        current_time = time.time()
        if current_time - self.last_optimization_time > self.optimization_interval:
            self.save_metrics()
            self.optimize_system()
            self.last_optimization_time = current_time
        
        # Basculer vers CPU si surchauffe
        if stats["temperature"] > self.max_temp:
            if self.using_gpu:
                logging.warning(f"Surchauffe détectée ({stats['temperature']}°C), désactivation du GPU")
                self.using_gpu = False
        
        return stats
    
    def save_metrics(self):
        """Enregistre les métriques dans un fichier JSON"""
        try:
            # Charger les métriques existantes
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            else:
                existing_metrics = []
                
            # Ajouter les nouvelles métriques
            existing_metrics.extend(self.metrics_history)
            
            # Limiter la taille du fichier (garder les 1000 dernières entrées)
            if len(existing_metrics) > 1000:
                existing_metrics = existing_metrics[-1000:]
                
            # Enregistrer
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f)
                
            # Vider l'historique local
            self.metrics_history = []
            
            logging.debug("Métriques enregistrées avec succès")
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement des métriques: {e}")
    
    def optimize_system(self):
        """Optimise les ressources système"""
        try:
            # Nettoyage de la mémoire sur macOS
            if platform.system() == "Darwin":
                subprocess.run(["sudo", "purge"], check=False)
                
            # Ajuster la priorité des processus
            for proc in psutil.process_iter(['pid', 'name']):
                if "ollama" in proc.info['name'].lower():
                    try:
                        # Augmenter la priorité d'Ollama
                        p = psutil.Process(proc.info['pid'])
                        if platform.system() == "Darwin":
                            subprocess.run(["sudo", "renice", "-n", "-10", "-p", str(proc.info['pid'])], check=False)
                    except Exception as e:
                        logging.error(f"Erreur lors de l'ajustement de la priorité: {e}")
        except Exception as e:
            logging.error(f"Erreur lors de l'optimisation du système: {e}")
    
    def handle_error(self, error: Exception):
        """Gère les erreurs liées aux ressources"""
        logging.error(f"Erreur détectée: {error}")
        
        # Vérifier si c'est une erreur de mémoire
        if isinstance(error, MemoryError) or "memory" in str(error).lower():
            logging.warning("Erreur de mémoire détectée, tentative de libération...")
            self.optimize_system()
            
        # Enregistrer l'erreur dans les métriques
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__
        })
        
        # Sauvegarder immédiatement
        self.save_metrics()
    
    def get_resource_report(self) -> str:
        """Génère un rapport détaillé des ressources"""
        resources = self.monitor_resources()
        
        report = [
            "=== Rapport des Ressources Système ===",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"CPU: {resources['cpu_percent']}% utilisé",
            f"Fréquence CPU: {resources['cpu_freq_mhz']} MHz",
            f"RAM: {resources['ram_used_percent']}% utilisé ({resources['ram_available_gb']:.2f} GB disponible)",
            f"Température: {resources['temperature']}°C",
            f"GPU disponible: {'Oui' if resources['gpu_available'] else 'Non'}",
            "=== Fin du Rapport ==="
        ]
        
        return "\n".join(report)
    
    def check_resources(self) -> bool:
        """
        Vérifie si les ressources système sont suffisantes pour exécuter une tâche
        
        Returns:
            bool: True si les ressources sont suffisantes, False sinon
        """
        resources = self.monitor_resources()
        
        # Vérifier les ressources
        has_enough_resources = (
            resources["cpu_percent"] < self.max_cpu_percent and
            resources["ram_available_gb"] > self.min_ram_gb and
            resources["temperature"] < self.max_temp
        )
        
        if not has_enough_resources:
            logging.warning(
                f"Ressources insuffisantes: CPU {resources['cpu_percent']}%, "
                f"RAM {resources['ram_available_gb']:.2f} GB, "
                f"Température {resources['temperature']}°C"
            )
        
        return has_enough_resources
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de ressources
        
        Returns:
            Dict[str, Any]: Statistiques de ressources
        """
        resources = self.monitor_resources()
        
        # Calculer quelques statistiques supplémentaires
        if self.metrics_history:
            avg_cpu = sum(m.get("cpu_percent", 0) for m in self.metrics_history) / len(self.metrics_history)
            avg_ram = sum(m.get("ram_used_percent", 0) for m in self.metrics_history) / len(self.metrics_history)
            avg_temp = sum(m.get("temperature", 0) for m in self.metrics_history) / len(self.metrics_history)
        else:
            avg_cpu = resources["cpu_percent"]
            avg_ram = resources["ram_used_percent"]
            avg_temp = resources["temperature"]
        
        return {
            "current": resources,
            "averages": {
                "cpu_percent": avg_cpu,
                "ram_used_percent": avg_ram,
                "temperature": avg_temp
            },
            "thresholds": {
                "max_cpu_percent": self.max_cpu_percent,
                "min_ram_gb": self.min_ram_gb,
                "max_temp": self.max_temp
            },
            "gpu_available": self.using_gpu,
            "metrics_count": len(self.metrics_history)
        }
