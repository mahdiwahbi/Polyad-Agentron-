import asyncio
import logging
from typing import Dict, Any
import psutil
import time
from dataclasses import dataclass

@dataclass
class NetworkMetrics:
    upload: float
    download: float
    latency: float
    packet_loss: float

class NetworkOptimizer:
    def __init__(self, config: Dict[str, Any]):
        """
        Optimiseur réseau
        
        Args:
            config (Dict[str, Any]): Configuration de l'optimiseur réseau
        """
        self.config = config
        self.logger = logging.getLogger('polyad.network')
        self.upload_threshold = config.get('upload_threshold', 10)  # Mbps
        self.download_threshold = config.get('download_threshold', 100)  # Mbps
        self.latency_threshold = config.get('latency_threshold', 100)  # ms
        self.packet_loss_threshold = config.get('packet_loss_threshold', 1)  # %
        self.optimization_interval = config.get('optimization_interval', 60)  # secondes
        self.last_optimization = time.time()
        self.metrics = NetworkMetrics(
            upload=0.0,
            download=0.0,
            latency=0.0,
            packet_loss=0.0
        )

    async def start(self) -> None:
        """
        Démarre la surveillance et l'optimisation réseau
        """
        self.logger.info("Démarrage de l'optimiseur réseau")
        while True:
            await self._optimize_network()
            await asyncio.sleep(self.optimization_interval)

    async def _optimize_network(self) -> None:
        """
        Optimise la performance réseau
        """
        try:
            # Mesurer les métriques actuelles
            metrics = self._get_network_metrics()
            
            # Vérifier les seuils
            if metrics.upload > self.upload_threshold:
                await self._optimize_upload()
            
            if metrics.download > self.download_threshold:
                await self._optimize_download()
            
            if metrics.latency > self.latency_threshold:
                await self._optimize_latency()
            
            if metrics.packet_loss > self.packet_loss_threshold:
                await self._optimize_packet_loss()
                
            # Mettre à jour les métriques
            self.metrics = metrics
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation réseau: {e}")

    def _get_network_metrics(self) -> NetworkMetrics:
        """
        Obtient les métriques réseau
        
        Returns:
            NetworkMetrics: Métriques réseau
        """
        # Mesurer le débit
        upload = psutil.net_io_counters().bytes_sent / 1e6  # en Mbps
        download = psutil.net_io_counters().bytes_recv / 1e6  # en Mbps
        
        # Mesurer la latence
        latency = self._measure_latency()
        
        # Mesurer la perte de paquets
        packet_loss = self._measure_packet_loss()
        
        return NetworkMetrics(
            upload=upload,
            download=download,
            latency=latency,
            packet_loss=packet_loss
        )

    def _measure_latency(self) -> float:
        """
        Mesure la latence réseau
        
        Returns:
            float: Latence en millisecondes
        """
        try:
            import subprocess
            result = subprocess.run(
                ['ping', '-c', '1', '8.8.8.8'],
                capture_output=True,
                text=True
            )
            # Extraire la latence de la sortie
            latency = float(result.stdout.split('time=')[1].split(' ')[0])
            return latency
            
        except Exception:
            return 1000  # 1 seconde par défaut

    def _measure_packet_loss(self) -> float:
        """
        Mesure la perte de paquets
        
        Returns:
            float: Perte de paquets en %
        """
        try:
            import subprocess
            result = subprocess.run(
                ['ping', '-c', '10', '8.8.8.8'],
                capture_output=True,
                text=True
            )
            # Extraire la perte de paquets de la sortie
            packet_loss = float(result.stdout.split('packet loss')[0].split(',')[-1].strip())
            return packet_loss
            
        except Exception:
            return 0  # 0% par défaut

    async def _optimize_upload(self) -> None:
        """
        Optimise le débit montant
        """
        self.logger.info("Optimisation du débit montant")
        try:
            # Réduire la taille des paquets
            self._set_mtu(1400)
            
            # Optimiser la compression
            self._enable_compression()
            
            # Limiter le nombre de connexions simultanées
            self._limit_connections()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation du débit montant: {e}")

    async def _optimize_download(self) -> None:
        """
        Optimise le débit descendant
        """
        self.logger.info("Optimisation du débit descendant")
        try:
            # Augmenter la taille des tampons
            self._increase_buffers()
            
            # Optimiser la connexion TCP
            self._optimize_tcp()
            
            # Activer la pré-chargement
            self._enable_prefetch()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation du débit descendant: {e}")

    async def _optimize_latency(self) -> None:
        """
        Optimise la latence
        """
        self.logger.info("Optimisation de la latence")
        try:
            # Optimiser la qualité de service
            self._optimize_qos()
            
            # Réduire la taille des paquets
            self._set_mtu(1200)
            
            # Activer la déduplication
            self._enable_deduplication()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation de la latence: {e}")

    async def _optimize_packet_loss(self) -> None:
        """
        Optimise la perte de paquets
        """
        self.logger.info("Optimisation de la perte de paquets")
        try:
            # Augmenter la redondance
            self._increase_redundancy()
            
            # Optimiser la correction d'erreurs
            self._optimize_error_correction()
            
            # Réduire la taille des paquets
            self._set_mtu(1000)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation de la perte de paquets: {e}")

    def _set_mtu(self, size: int) -> None:
        """
        Définit la taille du MTU
        
        Args:
            size (int): Taille du MTU
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'ifconfig', 'en0', 'mtu', str(size)
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration du MTU: {e}")

    def _enable_compression(self) -> None:
        """
        Active la compression
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_compression=1'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation de la compression: {e}")

    def _limit_connections(self) -> None:
        """
        Limite les connexions simultanées
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_max_syn_backlog=1024'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de la limitation des connexions: {e}")

    def _increase_buffers(self) -> None:
        """
        Augmente la taille des tampons
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.core.rmem_max=16777216'
            ])
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.core.wmem_max=16777216'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'augmentation des tampons: {e}")

    def _optimize_tcp(self) -> None:
        """
        Optimise la connexion TCP
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_window_scaling=1'
            ])
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_timestamps=1'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation TCP: {e}")

    def _enable_prefetch(self) -> None:
        """
        Active le pré-chargement
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_fastopen=1'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation du pré-chargement: {e}")

    def _optimize_qos(self) -> None:
        """
        Optimise la qualité de service
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'tc', 'qdisc', 'add', 'dev', 'en0', 'root', 'htb',
                'default', '1', 'r2q', '10'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation QoS: {e}")

    def _enable_deduplication(self) -> None:
        """
        Active la déduplication
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_sack=1'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation de la déduplication: {e}")

    def _increase_redundancy(self) -> None:
        """
        Augmente la redondance
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_reordering=3'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'augmentation de la redondance: {e}")

    def _optimize_error_correction(self) -> None:
        """
        Optimise la correction d'erreurs
        """
        try:
            import subprocess
            subprocess.run([
                'sudo', 'sysctl', '-w', 'net.ipv4.tcp_retries2=15'
            ])
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation de la correction d'erreurs: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtient les métriques réseau
        
        Returns:
            Dict[str, Any]: Métriques réseau
        """
        return {
            'upload': self.metrics.upload,
            'download': self.metrics.download,
            'latency': self.metrics.latency,
            'packet_loss': self.metrics.packet_loss
        }
