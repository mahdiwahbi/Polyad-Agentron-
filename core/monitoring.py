from typing import Dict, Any, Optional
import logging
import prometheus_client
from prometheus_client import Gauge, Counter
from grafana_api.grafana_face import GrafanaFace
import asyncio
import time
import psutil
import smc
import os
import json
from datetime import datetime

logger = logging.getLogger('polyad.monitoring')

class MonitoringService:
    def __init__(self, config: Dict[str, Any]):
        """Initialise le service de monitoring"""
        self.config = config
        self.logger = logging.getLogger('polyad.monitoring')
        
        # Initialiser les métriques Prometheus
        self.metrics = {
            'cpu': Gauge('polyad_cpu_usage', 'CPU usage percentage'),
            'memory': Gauge('polyad_memory_usage', 'Memory usage percentage'),
            'gpu': Gauge('polyad_gpu_usage', 'GPU usage percentage'),
            'temperature': Gauge('polyad_temperature', 'System temperature'),
            'disk': Gauge('polyad_disk_usage', 'Disk usage percentage'),
            'network_in': Gauge('polyad_network_in', 'Network incoming traffic'),
            'network_out': Gauge('polyad_network_out', 'Network outgoing traffic'),
            'processes': Gauge('polyad_active_processes', 'Number of active processes'),
            'requests': Counter('polyad_requests_total', 'Total number of requests processed'),
            'errors': Counter('polyad_errors_total', 'Total number of errors'),
            'response_time': Gauge('polyad_response_time_ms', 'Response time in milliseconds'),
            'gpu_memory': Gauge('polyad_gpu_memory', 'GPU memory usage percentage'),
            'swap': Gauge('polyad_swap_usage', 'Swap usage percentage'),
            'rl_reward': Gauge('polyad_rl_reward', 'Reinforcement Learning reward'),
            'lstm_memory': Gauge('polyad_lstm_memory', 'LSTM memory usage')
        }
        
        # Configuration Grafana
        self.grafana = GrafanaFace(
            auth=config.get('grafana_api_key'),
            host=config.get('grafana_host', 'localhost'),
            port=config.get('grafana_port', 3000)
        )
        
        # État de surveillance
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.last_metrics_update = time.time()
        self.metrics_update_interval = config.get('metrics_interval', 1)  # secondes
        self.alert_thresholds = config.get('alert_thresholds', {
            'cpu': 90,
            'memory': 90,
            'temperature': 80,
            'disk': 90,
            'network': 90,
            'rl_reward': -1.0,
            'lstm_memory': 90
        })
        
        # Logs
        self.metrics_log = []
        self.log_file = 'metrics.json'
        self.max_log_size = 10000  # Nombre maximum d'entrées

    async def initialize(self) -> bool:
        """Initialise le service de monitoring"""
        try:
            # Vérifier la connexion Grafana
            if self.config.get('grafana_api_key'):
                await self._test_grafana_connection()
            
            # Créer le dossier de logs s'il n'existe pas
            os.makedirs('logs', exist_ok=True)
            
            self.logger.info("Service de monitoring initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Échec de l'initialisation: {e}")
            return False

    async def start(self) -> None:
        """Démarre la surveillance"""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_metrics())
        
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

    async def _monitor_metrics(self) -> None:
        """Surveille les métriques en continu"""
        while self.is_running:
            try:
                # Mettre à jour les métriques
                metrics = self._collect_metrics()
                self._update_prometheus_metrics(metrics)
                
                # Sauvegarder les métriques
                self._save_metrics(metrics)
                
                # Vérifier les alertes
                self._check_alerts(metrics)
                
                # Envoyer les métriques à Grafana
                await self._send_metrics_to_grafana(metrics)
                
                await asyncio.sleep(self.metrics_update_interval)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance: {e}")
                await asyncio.sleep(5)  # Attendre plus longtemps en cas d'erreur

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collecte toutes les métriques du système"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'swap': psutil.swap_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'processes': len(psutil.pids()),
            'network': self._get_network_metrics(),
            'temperature': self._get_temperature(),
            'gpu': self._get_gpu_metrics(),
            'rl_reward': self._get_rl_reward(),
            'lstm_memory': self._get_lstm_memory_usage()
        }
        return metrics

    def _get_network_metrics(self) -> Dict[str, float]:
        """Récupère les métriques réseau"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }

    def _get_temperature(self) -> float:
        """Récupère la température du système"""
        try:
            smc = smc.SMC()
            temp = smc.read_key('TC0P')  # Température CPU
            return temp / 65536.0
        except:
            return 0.0

    def _get_gpu_metrics(self) -> Dict[str, float]:
        """Récupère les métriques GPU"""
        try:
            # Pour macOS avec Metal
            from metal import Metal
            gpu = Metal.get_default_device()
            memory = gpu.memory_used() / gpu.memory_total() * 100
            return {
                'memory': memory
            }
        except:
            return {
                'memory': 0.0
            }

    def _get_rl_reward(self) -> float:
        """Récupère la récompense RL moyenne"""
        # Implémenter la récupération de la récompense RL
        return 0.0

    def _get_lstm_memory_usage(self) -> float:
        """Récupère l'utilisation de la mémoire LSTM"""
        # Implémenter la récupération de l'utilisation de la mémoire LSTM
        return 0.0

    def _update_prometheus_metrics(self, metrics: Dict[str, Any]) -> None:
        """Met à jour les métriques Prometheus"""
        self.metrics['cpu'].set(metrics['cpu'])
        self.metrics['memory'].set(metrics['memory'])
        self.metrics['swap'].set(metrics['swap'])
        self.metrics['disk'].set(metrics['disk'])
        self.metrics['processes'].set(metrics['processes'])
        self.metrics['network_in'].set(metrics['network']['bytes_recv'])
        self.metrics['network_out'].set(metrics['network']['bytes_sent'])
        self.metrics['temperature'].set(metrics['temperature'])
        self.metrics['gpu_memory'].set(metrics['gpu']['memory'])
        self.metrics['rl_reward'].set(metrics['rl_reward'])
        self.metrics['lstm_memory'].set(metrics['lstm_memory'])

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Sauvegarde les métriques dans un fichier JSON"""
        self.metrics_log.append(metrics)
        if len(self.metrics_log) > self.max_log_size:
            self.metrics_log = self.metrics_log[-self.max_log_size:]
            
        with open(self.log_file, 'w') as f:
            json.dump(self.metrics_log, f)

    def _check_alerts(self, metrics: Dict[str, Any]) -> None:
        """Vérifie et déclenche les alertes si nécessaire"""
        alerts = []
        
        if metrics['cpu'] > self.alert_thresholds['cpu']:
            alerts.append({
                'type': 'cpu',
                'value': metrics['cpu'],
                'threshold': self.alert_thresholds['cpu']
            })
        
        if metrics['memory'] > self.alert_thresholds['memory']:
            alerts.append({
                'type': 'memory',
                'value': metrics['memory'],
                'threshold': self.alert_thresholds['memory']
            })
        
        if metrics['temperature'] > self.alert_thresholds['temperature']:
            alerts.append({
                'type': 'temperature',
                'value': metrics['temperature'],
                'threshold': self.alert_thresholds['temperature']
            })
        
        if metrics['disk'] > self.alert_thresholds['disk']:
            alerts.append({
                'type': 'disk',
                'value': metrics['disk'],
                'threshold': self.alert_thresholds['disk']
            })
        
        if metrics['network']['bytes_sent'] > self.alert_thresholds['network']:
            alerts.append({
                'type': 'network',
                'value': metrics['network']['bytes_sent'],
                'threshold': self.alert_thresholds['network']
            })
        
        if metrics['rl_reward'] < self.alert_thresholds['rl_reward']:
            alerts.append({
                'type': 'rl_reward',
                'value': metrics['rl_reward'],
                'threshold': self.alert_thresholds['rl_reward']
            })
        
        if metrics['lstm_memory'] > self.alert_thresholds['lstm_memory']:
            alerts.append({
                'type': 'lstm_memory',
                'value': metrics['lstm_memory'],
                'threshold': self.alert_thresholds['lstm_memory']
            })
        
        # Gérer les alertes (à implémenter selon les besoins)
        if alerts:
            self._handle_alerts(alerts)

    def _handle_alerts(self, alerts: list) -> None:
        """Gère les alertes déclenchées"""
        for alert in alerts:
            self.logger.warning(
                f"Alerte {alert['type'].upper()}: {alert['value']}% (Seuil: {alert['threshold']}%)"
            )
            # Ici, implémenter la notification via l'interface utilisateur

    async def _send_metrics_to_grafana(self, metrics: Dict[str, Any]) -> None:
        """Envoye les métriques à Grafana"""
        try:
            if self.config.get('grafana_api_key'):
                # Implémenter l'envoi des métriques à Grafana
                pass
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi à Grafana: {e}")

    async def _test_grafana_connection(self) -> None:
        """Teste la connexion à Grafana"""
        try:
            self.grafana.search.search_dashboards()
            self.logger.info("Connexion Grafana réussie")
        except Exception as e:
            self.logger.error(f"Échec de la connexion Grafana: {e}")

    def get_recent_metrics(self, limit: int = 100) -> list:
        """Retourne les métriques récentes"""
        return self.metrics_log[-limit:]

    def get_current_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques actuelles"""
        return self._collect_metrics()
