from typing import Dict, Any, Optional
import psutil
import platform
import json
import os
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass
import time
from utils.logger import logger

@dataclass
class ResourceQuota:
    """Définition d'un quota de ressources"""
    cpu: float = 100.0  # %
    memory: float = 100.0  # %
    disk: float = 100.0  # %
    network: float = 100.0  # %
    gpu: float = 100.0  # %

class ResourceManager:
    """Gestionnaire de ressources système avec monitoring et optimisation"""
    
    def __init__(self):
        """Initialise le gestionnaire de ressources"""
        self.logger = logging.getLogger('polyad.resources')
        self.logger.setLevel(logging.DEBUG)
        
        # Seuils de performance
        self.thresholds = {
            'cpu': {
                'warning': 80,  # %
                'critical': 90
            },
            'memory': {
                'warning': 80,  # %
                'critical': 90
            },
            'temperature': {
                'warning': 80,  # °C
                'critical': 90
            },
            'disk': {
                'warning': 80,  # %
                'critical': 90
            },
            'network': {
                'warning': 90,  # %
                'critical': 95
            }
        }
        
        # Historique des métriques
        self.metrics_history = []
        self.current_metrics = {}
        
        # État de surveillance
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Optimisation des ressources
        self.optimization_interval = 60  # secondes
        self.last_optimization_time = time.time()
        
        # Gestion des quotas
        self.user_quotas: Dict[str, ResourceQuota] = {}
        self.global_quota = ResourceQuota()
        
        # Limites de ressources
        self.resource_limits = {
            'max_memory_gb': 16,  # Go
            'max_cpu_cores': psutil.cpu_count(),
            'max_disk_gb': 1024,  # Go
            'max_network_mbps': 1000  # Mbps
        }

    def set_user_quota(self, user_id: str, quota: ResourceQuota) -> None:
        """Définit un quota pour un utilisateur"""
        self.user_quotas[user_id] = quota

    def get_user_quota(self, user_id: str) -> Optional[ResourceQuota]:
        """Obtient le quota d'un utilisateur"""
        return self.user_quotas.get(user_id)

    def check_resource_limits(self, user_id: str, metrics: Dict[str, Any]) -> bool:
        """Vérifie les limites de ressources pour un utilisateur"""
        user_quota = self.get_user_quota(user_id)
        if not user_quota:
            user_quota = self.global_quota

        # Vérifier les limites CPU
        if metrics['cpu']['percent'] > user_quota.cpu:
            return False

        # Vérifier les limites mémoire
        memory_percent = metrics['memory']['ram']['percent']
        if memory_percent > user_quota.memory:
            return False

        # Vérifier les limites disque
        disk_percent = metrics['disk']['percent']
        if disk_percent > user_quota.disk:
            return False

        # Vérifier les limites réseau
        network_usage = (metrics['network']['bytes_sent'] + 
                       metrics['network']['bytes_recv']) / 1_000_000  # en Mbps
        if network_usage > user_quota.network:
            return False

        return True

    async def optimize_resources(self) -> None:
        """Optimise les ressources du système"""
        current_time = time.time()
        if current_time - self.last_optimization_time < self.optimization_interval:
            return

        self.last_optimization_time = current_time
        
        # Optimisation de la mémoire
        if self.current_metrics.get('memory', {}).get('ram', {}).get('percent', 0) > 80:
            await self._cleanup_memory()
            
        # Optimisation CPU
        if self.current_metrics.get('cpu', {}).get('percent', 0) > 80:
            await self._optimize_cpu()

        # Optimisation disque
        if self.current_metrics.get('disk', {}).get('percent', 0) > 80:
            await self._optimize_disk()

        # Optimisation réseau
        if self.current_metrics.get('network', {}).get('percent', 0) > 80:
            await self._optimize_network()

    async def _cleanup_memory(self) -> None:
        """Nettoie la mémoire"""
        try:
            # Forcer la libération de la mémoire
            psutil.Process().memory_percent()
            os.system('sync')
            os.system('echo 3 > /proc/sys/vm/drop_caches')
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage de la mémoire: {e}")

    async def _optimize_cpu(self) -> None:
        """Optimise l'utilisation du CPU"""
        try:
            # Réduire la priorité des processus non-critiques
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                if proc.info['cpu_percent'] > 50:
                    try:
                        proc.nice(19)  # Réduire la priorité
                    except:
                        pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation CPU: {e}")

    async def _optimize_disk(self) -> None:
        """Optimise l'utilisation du disque"""
        try:
            # Nettoyer les fichiers temporaires
            os.system('rm -rf /tmp/*')
            os.system('rm -rf /var/tmp/*')
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation disque: {e}")

    async def _optimize_network(self) -> None:
        """Optimise l'utilisation du réseau"""
        try:
            # Limiter le débit des connexions non-critiques
            pass  # À implémenter selon les besoins
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation réseau: {e}")

    def get_resource_usage(self, user_id: str) -> Dict[str, Any]:
        """Obtient l'utilisation des ressources pour un utilisateur"""
        metrics = self.current_metrics.copy()
        user_quota = self.get_user_quota(user_id)
        
        if user_quota:
            metrics['quota'] = {
                'cpu': user_quota.cpu,
                'memory': user_quota.memory,
                'disk': user_quota.disk,
                'network': user_quota.network,
                'gpu': user_quota.gpu
            }
        
        return metrics

    def get_system_limits(self) -> Dict[str, Any]:
        """Obtient les limites de ressources du système"""
        return {
            'cpu': {
                'cores': psutil.cpu_count(),
                'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else 0
            },
            'memory': {
                'total_gb': psutil.virtual_memory().total / (1024**3)
            },
            'disk': {
                'total_gb': psutil.disk_usage('/').total / (1024**3)
            },
            'network': {
                'max_mbps': self.resource_limits['max_network_mbps']
            }
        }

    async def start(self) -> None:
        """Démarre la surveillance des ressources"""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_resources())
        
    async def stop(self) -> None:
        """Arrête la surveillance"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_resources(self) -> None:
        """Surveille les ressources en continu"""
        while self.is_running:
            try:
                metrics = await self.get_system_info()
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # Optimisation des ressources
                await self.optimize_resources()
                
                await asyncio.sleep(1)  # Attendre 1 seconde
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance: {e}")
                await asyncio.sleep(5)  # Attendre plus longtemps en cas d'erreur

    async def get_system_info(self) -> Dict[str, Any]:
        """Obtenir les informations système"""
        try:
            info = {
                'os_type': platform.system(),
                'os_release': platform.release(),
                'cpu_cores': psutil.cpu_count(),
                'ram_gb': psutil.virtual_memory().total / (1024**3),
                'gpu_memory': self._get_gpu_memory()
            }
            return info
            
        except Exception as e:
            logger.error(f"Erreur de récupération des infos système: {e}")
            return {}
            
    def _get_gpu_memory(self) -> float:
        """Obtenir la mémoire GPU disponible"""
        try:
            # À implémenter selon le GPU
            return 0
            
        except Exception:
            return 0
            
    def _get_temperature(self) -> Dict[str, float]:
        """Obtenir les températures système"""
        try:
            temps = {}
            if hasattr(psutil, "sensors_temperatures"):
                for name, entries in psutil.sensors_temperatures().items():
                    if entries:
                        temps[name] = entries[0].current
            return temps
            
        except Exception:
            return {}
            
    async def monitor(self) -> Dict[str, Any]:
        """Monitorer les ressources système"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'ram': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent
                    },
                    'swap': {
                        'total': psutil.swap_memory().total,
                        'used': psutil.swap_memory().used,
                        'percent': psutil.swap_memory().percent
                    }
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'percent': psutil.disk_usage('/').percent
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                },
                'temperature': self._get_temperature()
            }
            
            # Sauvegarder les métriques
            self.metrics_history.append(metrics)
            self.current_metrics = metrics
            
            # Vérifier les seuils
            self._check_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur de monitoring: {e}")
            return {}
            
    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Vérifier les seuils critiques"""
        try:
            # CPU
            if metrics['cpu']['percent'] >= self.thresholds['cpu']['critical']:
                logger.warning("Utilisation CPU critique!")
                
            # Mémoire
            if metrics['memory']['ram']['percent'] >= self.thresholds['memory']['critical']:
                logger.warning("Utilisation mémoire critique!")
                
            # Température
            for device, temp in metrics['temperature'].items():
                if temp >= self.thresholds['temperature']['critical']:
                    logger.warning(f"Température critique pour {device}!")
                    
        except Exception as e:
            logger.error(f"Erreur de vérification des seuils: {e}")
            
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtient les métriques actuelles"""
        return self.current_metrics.copy()

    def get_metrics_history(self) -> list:
        """Obtient l'historique des métriques"""
        return self.metrics_history.copy()

    async def save_metrics(self):
        """Sauvegarder l'historique des métriques"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(os.path.join('data', 'metrics_history.json'), 'w') as f:
                json.dump(self.metrics_history[-1000:], f)  # Garder les 1000 dernières
                
        except Exception as e:
            logger.error(f"Erreur de sauvegarde des métriques: {e}")
            
    def __len__(self):
        """Nombre de métriques dans l'historique"""
        return len(self.metrics_history)
