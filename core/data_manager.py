import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from utils.logger import logger

class DataManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.data')
        
        # Configuration des données
        self.data_config = config.get('data', {
            'base_dir': 'data',
            'version_dir': 'versions',
            'archive_dir': 'archive',
            'backup_dir': 'backup',
            'max_versions': 10,
            'max_archives': 100,
            'cleanup_interval': 86400,  # 24 heures
            'compression_level': 9
        })
        
        # Initialiser les répertoires
        self._init_directories()
        
        # Historique des opérations
        self.operation_history = []

    def _init_directories(self):
        """Initialise les répertoires nécessaires"""
        base_dir = self.data_config['base_dir']
        
        # Créer les répertoires principaux
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(os.path.join(base_dir, self.data_config['version_dir']), exist_ok=True)
        os.makedirs(os.path.join(base_dir, self.data_config['archive_dir']), exist_ok=True)
        os.makedirs(os.path.join(base_dir, self.data_config['backup_dir']), exist_ok=True)

    def create_version(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Crée une nouvelle version des données"""
        version_dir = os.path.join(self.data_config['base_dir'], self.data_config['version_dir'])
        timestamp = datetime.now().isoformat()
        version_id = f"v_{timestamp}"
        
        # Sauvegarder les données
        data_path = os.path.join(version_dir, f"{version_id}.json")
        with open(data_path, 'w') as f:
            json.dump(data, f)
        
        # Sauvegarder les métadonnées
        metadata_path = os.path.join(version_dir, f"{version_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Nettoyer les versions anciennes
        self._cleanup_versions()
        
        # Enregistrer l'opération
        self.operation_history.append({
            'type': 'version',
            'id': version_id,
            'timestamp': timestamp,
            'metadata': metadata
        })
        
        return version_id

    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Obtient une version spécifique des données"""
        version_dir = os.path.join(self.data_config['base_dir'], self.data_config['version_dir'])
        data_path = os.path.join(version_dir, f"{version_id}.json")
        
        if not os.path.exists(data_path):
            return None
            
        with open(data_path, 'r') as f:
            return json.load(f)

    def archive_data(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Archive les données"""
        archive_dir = os.path.join(self.data_config['base_dir'], self.data_config['archive_dir'])
        timestamp = datetime.now().isoformat()
        archive_id = f"a_{timestamp}"
        
        # Sauvegarder les données
        archive_path = os.path.join(archive_dir, f"{archive_id}.json")
        with open(archive_path, 'w') as f:
            json.dump(data, f)
        
        # Sauvegarder les métadonnées
        metadata_path = os.path.join(archive_dir, f"{archive_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Nettoyer les archives anciennes
        self._cleanup_archives()
        
        # Enregistrer l'opération
        self.operation_history.append({
            'type': 'archive',
            'id': archive_id,
            'timestamp': timestamp,
            'metadata': metadata
        })
        
        return archive_id

    def get_archive(self, archive_id: str) -> Optional[Dict[str, Any]]:
        """Obtient une archive spécifique"""
        archive_dir = os.path.join(self.data_config['base_dir'], self.data_config['archive_dir'])
        archive_path = os.path.join(archive_dir, f"{archive_id}.json")
        
        if not os.path.exists(archive_path):
            return None
            
        with open(archive_path, 'r') as f:
            return json.load(f)

    def _cleanup_versions(self):
        """Nettoie les versions anciennes"""
        version_dir = os.path.join(self.data_config['base_dir'], self.data_config['version_dir'])
        versions = os.listdir(version_dir)
        
        # Trier les versions par date
        versions.sort(reverse=True)
        
        # Supprimer les versions au-delà du nombre maximum
        if len(versions) > self.data_config['max_versions'] * 2:  # Compte les fichiers de données et de métadonnées
            for version in versions[self.data_config['max_versions'] * 2:]:
                try:
                    os.remove(os.path.join(version_dir, version))
                except:
                    self.logger.error(f"Erreur lors de la suppression de la version {version}")

    def _cleanup_archives(self):
        """Nettoie les archives anciennes"""
        archive_dir = os.path.join(self.data_config['base_dir'], self.data_config['archive_dir'])
        archives = os.listdir(archive_dir)
        
        # Trier les archives par date
        archives.sort(reverse=True)
        
        # Supprimer les archives au-delà du nombre maximum
        if len(archives) > self.data_config['max_archives'] * 2:  # Compte les fichiers de données et de métadonnées
            for archive in archives[self.data_config['max_archives'] * 2:]:
                try:
                    os.remove(os.path.join(archive_dir, archive))
                except:
                    self.logger.error(f"Erreur lors de la suppression de l'archive {archive}")

    def create_backup(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Crée un backup des données"""
        backup_dir = os.path.join(self.data_config['base_dir'], self.data_config['backup_dir'])
        timestamp = datetime.now().isoformat()
        backup_id = f"b_{timestamp}"
        
        # Sauvegarder les données
        backup_path = os.path.join(backup_dir, f"{backup_id}.json")
        with open(backup_path, 'w') as f:
            json.dump(data, f)
        
        # Sauvegarder les métadonnées
        metadata_path = os.path.join(backup_dir, f"{backup_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Enregistrer l'opération
        self.operation_history.append({
            'type': 'backup',
            'id': backup_id,
            'timestamp': timestamp,
            'metadata': metadata
        })
        
        return backup_id

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Obtient un backup spécifique"""
        backup_dir = os.path.join(self.data_config['base_dir'], self.data_config['backup_dir'])
        backup_path = os.path.join(backup_dir, f"{backup_id}.json")
        
        if not os.path.exists(backup_path):
            return None
            
        with open(backup_path, 'r') as f:
            return json.load(f)

    def restore_backup(self, backup_id: str) -> bool:
        """Restaure un backup"""
        backup_dir = os.path.join(self.data_config['base_dir'], self.data_config['backup_dir'])
        backup_path = os.path.join(backup_dir, f"{backup_id}.json")
        
        if not os.path.exists(backup_path):
            return False
            
        # Lire les données du backup
        with open(backup_path, 'r') as f:
            data = json.load(f)
        
        # Restaurer les données
        try:
            # Implémentation spécifique selon le type de données
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors de la restauration du backup {backup_id}: {e}")
            return False
        
        # Enregistrer l'opération
        self.operation_history.append({
            'type': 'restore',
            'id': backup_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return True

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Obtient l'historique des opérations"""
        return self.operation_history.copy()

    def get_data_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des données"""
        version_dir = os.path.join(self.data_config['base_dir'], self.data_config['version_dir'])
        archive_dir = os.path.join(self.data_config['base_dir'], self.data_config['archive_dir'])
        backup_dir = os.path.join(self.data_config['base_dir'], self.data_config['backup_dir'])
        
        return {
            'versions': {
                'count': len(os.listdir(version_dir)) // 2,  # Compte les paires de fichiers
                'max_versions': self.data_config['max_versions']
            },
            'archives': {
                'count': len(os.listdir(archive_dir)) // 2,
                'max_archives': self.data_config['max_archives']
            },
            'backups': {
                'count': len(os.listdir(backup_dir)) // 2,
                'last_backup': self.operation_history[-1]['timestamp'] if self.operation_history else None
            },
            'operations': {
                'total': len(self.operation_history),
                'last_operation': self.operation_history[-1]['timestamp'] if self.operation_history else None
            }
        }
