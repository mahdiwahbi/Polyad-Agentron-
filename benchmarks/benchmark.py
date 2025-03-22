import time
import psutil
import torch
import numpy as np
from polyad.utils.config import load_config
from polyad.core.agent import PolyadAgent
from polyad.services.cache import CacheManager
from polyad.services.model import ModelManager
from polyad.services.monitoring import MonitoringService

class PerformanceBenchmark:
    def __init__(self):
        self.config = load_config()
        self.cache_manager = CacheManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.monitoring_service = MonitoringService(self.config)
        self.agent = PolyadAgent(
            config=self.config,
            cache_manager=self.cache_manager,
            model_manager=self.model_manager,
            monitoring_service=self.monitoring_service
        )

    def measure_memory_usage(self):
        """Mesure l'utilisation de la mémoire"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss": memory_info.rss / (1024 * 1024),  # en Mo
            "vms": memory_info.vms / (1024 * 1024),  # en Mo
            "shared": memory_info.shared / (1024 * 1024)  # en Mo
        }

    def measure_cpu_usage(self):
        """Mesure l'utilisation du CPU"""
        return psutil.cpu_percent(interval=1)

    def measure_gpu_usage(self):
        """Mesure l'utilisation du GPU"""
        if torch.cuda.is_available():
            return {
                "gpu_utilization": torch.cuda.utilization(),
                "memory_allocated": torch.cuda.memory_allocated() / (1024 * 1024),  # en Mo
                "memory_cached": torch.cuda.memory_reserved() / (1024 * 1024)  # en Mo
            }
        return None

    def benchmark_model_generation(self, num_iterations=100):
        """Benchmark la génération de texte"""
        prompts = [
            "Quelle est la capitale de la France?",
            "Explique le concept de l'intelligence artificielle.",
            "Comment fonctionne l'apprentissage profond?"
        ]

        results = {
            "total_time": 0,
            "avg_time": 0,
            "memory_usage": [],
            "cpu_usage": [],
            "gpu_usage": []
        }

        for _ in range(num_iterations):
            start_time = time.time()
            
            # Mesure avant la génération
            pre_memory = self.measure_memory_usage()
            pre_cpu = self.measure_cpu_usage()
            pre_gpu = self.measure_gpu_usage()

            # Génération
            for prompt in prompts:
                self.model_manager.generate(prompt)

            # Mesure après la génération
            post_memory = self.measure_memory_usage()
            post_cpu = self.measure_cpu_usage()
            post_gpu = self.measure_gpu_usage()

            end_time = time.time()

            # Calcul des métriques
            results["total_time"] += end_time - start_time
            results["memory_usage"].append({
                "rss": post_memory["rss"] - pre_memory["rss"],
                "vms": post_memory["vms"] - pre_memory["vms"]
            })
            results["cpu_usage"].append(post_cpu - pre_cpu)
            
            if pre_gpu:
                results["gpu_usage"].append({
                    "utilization": post_gpu["gpu_utilization"] - pre_gpu["gpu_utilization"],
                    "memory": post_gpu["memory_allocated"] - pre_gpu["memory_allocated"]
                })

        results["avg_time"] = results["total_time"] / num_iterations
        return results

    def benchmark_cache_performance(self, num_operations=1000):
        """Benchmark les performances du cache"""
        test_data = {f"key_{i}": f"value_{i}" for i in range(num_operations)}

        results = {
            "write_time": 0,
            "read_time": 0,
            "hit_rate": 0,
            "miss_rate": 0
        }

        # Écriture
        start_write = time.time()
        for key, value in test_data.items():
            self.cache_manager.set(key, value)
        results["write_time"] = time.time() - start_write

        # Lecture
        start_read = time.time()
        hits = 0
        for key in test_data.keys():
            if self.cache_manager.get(key) is not None:
                hits += 1
        results["read_time"] = time.time() - start_read
        
        results["hit_rate"] = hits / num_operations
        results["miss_rate"] = 1 - results["hit_rate"]

        return results

    def run_benchmarks(self):
        """Exécute tous les benchmarks"""
        print("\n=== Démarrage des benchmarks ===\n")

        print("Benchmark du modèle:")
        model_results = self.benchmark_model_generation()
        print(f"Temps moyen de génération: {model_results['avg_time']:.2f} s")
        print(f"Utilisation mémoire: {np.mean([m['rss'] for m in model_results['memory_usage']]):.2f} Mo")
        print(f"Utilisation CPU: {np.mean(model_results['cpu_usage']):.2f}%")
        
        if model_results.get("gpu_usage"):
            print(f"Utilisation GPU: {np.mean([g['utilization'] for g in model_results['gpu_usage']]):.2f}%")
            print(f"Utilisation mémoire GPU: {np.mean([g['memory'] for g in model_results['gpu_usage']]):.2f} Mo")

        print("\nBenchmark du cache:")
        cache_results = self.benchmark_cache_performance()
        print(f"Temps d'écriture: {cache_results['write_time']:.2f} s")
        print(f"Temps de lecture: {cache_results['read_time']:.2f} s")
        print(f"Taux de frappe: {cache_results['hit_rate']:.2%}")
        print(f"Taux de manque: {cache_results['miss_rate']:.2%}")

        print("\n=== Fin des benchmarks ===\n")

if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    benchmark.run_benchmarks()