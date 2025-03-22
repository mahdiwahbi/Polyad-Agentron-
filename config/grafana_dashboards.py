from typing import Dict, Any
import json
import logging
from pathlib import Path

class GrafanaDashboards:
    def __init__(self, config: Dict[str, Any]):
        """Initialise les dashboards Grafana
        
        Args:
            config (Dict[str, Any]): Configuration Grafana
        """
        self.config = config
        self.logger = logging.getLogger('polyad.grafana')
        self.dashboards_dir = Path(__file__).parent / 'dashboards'
        
    def get_dashboard(self, name: str) -> Dict[str, Any]:
        """Obtient un dashboard Grafana
        
        Args:
            name (str): Nom du dashboard
            
        Returns:
            Dict[str, Any]: Configuration du dashboard
        """
        try:
            dashboard_path = self.dashboards_dir / f"{name}.json"
            if not dashboard_path.exists():
                self.logger.warning(f"Dashboard non trouvé: {name}")
                return self._get_default_dashboard()
                
            with open(dashboard_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du dashboard: {e}")
            return self._get_default_dashboard()

    def _get_default_dashboard(self) -> Dict[str, Any]:
        """Obtient le dashboard par défaut
        
        Returns:
            Dict[str, Any]: Configuration du dashboard par défaut
        """
        return {
            "title": "Polyad Dashboard",
            "panels": [
                {
                    "title": "Performance Générale",
                    "panels": [
                        {
                            "title": "CPU Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_cpu_usage",
                                    "legendFormat": "CPU Usage"
                                }
                            ]
                        },
                        {
                            "title": "Memory Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_memory_usage",
                                    "legendFormat": "Memory Usage"
                                }
                            ]
                        }
                    ]
                },
                {
                    "title": "GPU Performance",
                    "panels": [
                        {
                            "title": "GPU Memory",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_gpu_memory_usage",
                                    "legendFormat": "GPU Memory"
                                }
                            ]
                        },
                        {
                            "title": "GPU Temperature",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_gpu_temperature",
                                    "legendFormat": "GPU Temperature"
                                }
                            ]
                        }
                    ]
                },
                {
                    "title": "Cache Performance",
                    "panels": [
                        {
                            "title": "Cache Hits",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_cache_hits",
                                    "legendFormat": "Cache Hits"
                                }
                            ]
                        },
                        {
                            "title": "Cache Misses",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_cache_misses",
                                    "legendFormat": "Cache Misses"
                                }
                            ]
                        }
                    ]
                },
                {
                    "title": "Network Performance",
                    "panels": [
                        {
                            "title": "Network Upload",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_network_upload",
                                    "legendFormat": "Upload"
                                }
                            ]
                        },
                        {
                            "title": "Network Download",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "polyad_network_download",
                                    "legendFormat": "Download"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def create_dashboard(self, name: str, dashboard: Dict[str, Any]) -> bool:
        """Crée un nouveau dashboard
        
        Args:
            name (str): Nom du dashboard
            dashboard (Dict[str, Any]): Configuration du dashboard
            
        Returns:
            bool: True si le dashboard a été créé
        """
        try:
            dashboard_path = self.dashboards_dir / f"{name}.json"
            with open(dashboard_path, 'w') as f:
                json.dump(dashboard, f, indent=2)
            self.logger.info(f"Dashboard créé: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du dashboard: {e}")
            return False

    def update_dashboard(self, name: str, updates: Dict[str, Any]) -> bool:
        """Met à jour un dashboard existant
        
        Args:
            name (str): Nom du dashboard
            updates (Dict[str, Any]): Mises à jour du dashboard
            
        Returns:
            bool: True si le dashboard a été mis à jour
        """
        try:
            dashboard = self.get_dashboard(name)
            dashboard.update(updates)
            return self.create_dashboard(name, dashboard)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour du dashboard: {e}")
            return False

    def delete_dashboard(self, name: str) -> bool:
        """Supprime un dashboard
        
        Args:
            name (str): Nom du dashboard
            
        Returns:
            bool: True si le dashboard a été supprimé
        """
        try:
            dashboard_path = self.dashboards_dir / f"{name}.json"
            if dashboard_path.exists():
                dashboard_path.unlink()
                self.logger.info(f"Dashboard supprimé: {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du dashboard: {e}")
            return False

    def list_dashboards(self) -> list:
        """Liste tous les dashboards disponibles
        
        Returns:
            list: Liste des noms des dashboards
        """
        try:
            return [f.stem for f in self.dashboards_dir.glob("*.json")]
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la liste des dashboards: {e}")
            return []
