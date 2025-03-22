import asyncio
import logging
from typing import Dict, Any, Optional
import os
import psutil
from prometheus_client import start_http_server, Gauge, Counter
from grafana_api.grafana_face import GrafanaFace
import json
from datetime import datetime

class MonitoringService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.monitoring')
        
        # Initialiser les métriques Prometheus
        self.metrics = {
            'cpu': Gauge('polyad_cpu_usage', 'CPU usage percentage'),
            'memory': Gauge('polyad_memory_usage', 'Memory usage percentage'),
            'gpu': Gauge('polyad_gpu_usage', 'GPU usage percentage'),
            'temperature': Gauge('polyad_temperature', 'System temperature'),
            'disk': Gauge('polyad_disk_usage', 'Disk usage percentage'),
            'network_in': Gauge('polyad_network_in', 'Network download rate'),
            'network_out': Gauge('polyad_network_out', 'Network upload rate')
        }
        
        # Configuration Grafana
        self.grafana_config = self.config.get('monitoring', {}).get('grafana', {})
        self.grafana = GrafanaFace(
            auth=self.grafana_config.get('api_key'),
            host=self.grafana_config.get('host', 'localhost'),
            port=self.grafana_config.get('port', 3000)
        )
        
        # État de surveillance
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.metrics_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'metrics.json')

    async def initialize(self):
        """Initialiser le service de surveillance"""
        self.logger.info("Initialisation du service de surveillance...")
        
        try:
            # Démarrer le serveur Prometheus
            prometheus_port = self.config.get('monitoring', {}).get('metrics_port', 9090)
            start_http_server(prometheus_port)
            self.logger.info(f"Serveur Prometheus démarré sur le port {prometheus_port}")
            
            # Créer le répertoire logs s'il n'existe pas
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de Prometheus : {str(e)}")
            raise

    async def start(self):
        """Démarrer la surveillance"""
        try:
            await self.initialize()
            self.is_running = True
            self.monitor_task = asyncio.create_task(self.monitor_system())
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage de la surveillance : {str(e)}")
            raise

    async def stop(self):
        """Arrêter la surveillance"""
        try:
            if self.monitor_task:
                self.monitor_task.cancel()
                await self.monitor_task
            self.is_running = False
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt de la surveillance : {str(e)}")

    async def monitor_system(self):
        """Surveiller le système"""
        last_net_io = psutil.net_io_counters()
        
        while self.is_running:
            try:
                # Récupérer les métriques
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu': {
                        'percent': psutil.cpu_percent(interval=1)
                    },
                    'memory': {
                        'percent': psutil.virtual_memory().percent
                    },
                    'temperature': psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current', 0) if hasattr(psutil, 'sensors_temperatures') else 0,
                    'disk': {
                        'percent': psutil.disk_usage('/').percent
                    },
                    'network': {
                        'bytes_recv': 0,
                        'bytes_sent': 0
                    }
                }
                
                # Calculer le débit réseau
                net_io = psutil.net_io_counters()
                metrics['network']['bytes_recv'] = net_io.bytes_recv - last_net_io.bytes_recv
                metrics['network']['bytes_sent'] = net_io.bytes_sent - last_net_io.bytes_sent
                last_net_io = net_io
                
                # Sauvegarder les métriques
                self.save_metrics(metrics)
                
                # Mettre à jour les métriques Prometheus
                self.metrics['cpu'].set(metrics['cpu']['percent'])
                self.metrics['memory'].set(metrics['memory']['percent'])
                self.metrics['temperature'].set(metrics['temperature'])
                self.metrics['disk'].set(metrics['disk']['percent'])
                self.metrics['network_in'].set(metrics['network']['bytes_recv'])
                self.metrics['network_out'].set(metrics['network']['bytes_sent'])
                
                # Vérifier les seuils d'alerte
                alert_thresholds = self.config.get('monitoring', {}).get('alert_thresholds', {})
                
                if metrics['cpu']['percent'] > alert_thresholds.get('cpu', 90):
                    self.logger.warning(f"Alerte : Utilisation CPU élevée ({metrics['cpu']['percent']}%)")
                
                if metrics['memory']['percent'] > alert_thresholds.get('memory', 90):
                    self.logger.warning(f"Alerte : Utilisation mémoire élevée ({metrics['memory']['percent']}%)")
                
                if metrics['temperature'] > alert_thresholds.get('temperature', 80):
                    self.logger.warning(f"Alerte : Température élevée ({metrics['temperature']}°C)")
                
                if metrics['disk']['percent'] > alert_thresholds.get('disk', 90):
                    self.logger.warning(f"Alerte : Utilisation disque élevée ({metrics['disk']['percent']}%)")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la surveillance : {str(e)}")
                await asyncio.sleep(5)

    def save_metrics(self, metrics: Dict[str, Any]):
        """Sauvegarder les métriques dans un fichier JSON"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            data.append(metrics)
            
            # Limiter la taille du fichier
            if len(data) > 1000:
                data = data[-1000:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des métriques : {str(e)}")
