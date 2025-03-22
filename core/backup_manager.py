import os
import shutil
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import boto3
from utils.logger import logger

class BackupManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.backup')
        
        # Configuration des backups
        self.backup_config = config.get('backup', {
            'local_dir': 'backup',
            's3_bucket': 'polyad-backups',
            'retention_days': 30,
            'cleanup_interval': 86400,  # 24 heures
            'compression_level': 9,
            'encryption_key': None,
            'verify_integrity': True
        })
        
        # Initialiser S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key')
        )
        
        # Historique des backups
        self.backup_history = []
        
        # État des vérifications d'intégrité
        self.integrity_checks = {}

    def create_backup(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Crée un backup des données"""
        timestamp = datetime.now().isoformat()
        backup_id = f"backup_{timestamp}"
        
        # Sauvegarder les données localement
        local_path = os.path.join(self.backup_config['local_dir'], f"{backup_id}.json")
        self._save_to_file(data, local_path)
        
        # Sauvegarder les métadonnées
        metadata_path = os.path.join(self.backup_config['local_dir'], f"{backup_id}_metadata.json")
        self._save_to_file(metadata, metadata_path)
        
        # Calculer l'intégrité
        integrity = self._calculate_integrity(local_path)
        
        # Sauvegarder sur S3
        self._upload_to_s3(local_path, backup_id)
        
        # Enregistrer l'opération
        self.backup_history.append({
            'id': backup_id,
            'timestamp': timestamp,
            'size': os.path.getsize(local_path),
            'integrity': integrity,
            'metadata': metadata
        })
        
        # Nettoyer les backups anciens
        self._cleanup_old_backups()
        
        return backup_id

    def _save_to_file(self, data: Any, path: str) -> None:
        """Sauvegarde les données dans un fichier"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f)

    def _calculate_integrity(self, file_path: str) -> str:
        """Calcule l'intégrité d'un fichier"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _upload_to_s3(self, file_path: str, backup_id: str) -> None:
        """Upload un fichier sur S3"""
        try:
            self.s3_client.upload_file(
                file_path,
                self.backup_config['s3_bucket'],
                f"backups/{backup_id}.json",
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'backup_id': backup_id,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            )
        except Exception as e:
            self.logger.error(f"Erreur lors de l'upload sur S3: {e}")
            raise

    def _cleanup_old_backups(self) -> None:
        """Nettoie les backups anciens"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_config['retention_days'])
        
        # Nettoyer les backups locaux
        for backup_file in os.listdir(self.backup_config['local_dir']):
            if backup_file.startswith('backup_'):
                backup_path = os.path.join(self.backup_config['local_dir'], backup_file)
                backup_date = datetime.fromisoformat(backup_file.split('_')[1])
                if backup_date < cutoff_date:
                    try:
                        os.remove(backup_path)
                    except:
                        self.logger.error(f"Erreur lors de la suppression du backup {backup_file}")
        
        # Nettoyer les backups S3
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.backup_config['s3_bucket'],
                Prefix='backups/'
            )
            
            for obj in response.get('Contents', []):
                backup_date = datetime.fromisoformat(obj['Key'].split('/')[1].split('_')[1])
                if backup_date < cutoff_date:
                    try:
                        self.s3_client.delete_object(
                            Bucket=self.backup_config['s3_bucket'],
                            Key=obj['Key']
                        )
                    except:
                        self.logger.error(f"Erreur lors de la suppression du backup S3 {obj['Key']}")
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des backups S3: {e}")

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Vérifie l'intégrité d'un backup"""
        if backup_id in self.integrity_checks:
            return self.integrity_checks[backup_id]
            
        try:
            # Télécharger le backup S3
            local_path = os.path.join(self.backup_config['local_dir'], f"{backup_id}.json")
            self.s3_client.download_file(
                self.backup_config['s3_bucket'],
                f"backups/{backup_id}.json",
                local_path
            )
            
            # Vérifier l'intégrité
            integrity = self._calculate_integrity(local_path)
            
            # Comparer avec l'intégrité enregistrée
            for backup in self.backup_history:
                if backup['id'] == backup_id:
                    self.integrity_checks[backup_id] = integrity == backup['integrity']
                    return self.integrity_checks[backup_id]
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de l'intégrité: {e}")
            return False

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Obtient l'historique des backups"""
        return self.backup_history.copy()

    def get_backup_status(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Obtient le statut d'un backup spécifique"""
        for backup in self.backup_history:
            if backup['id'] == backup_id:
                return {
                    'id': backup['id'],
                    'timestamp': backup['timestamp'],
                    'size': backup['size'],
                    'integrity': backup['integrity'],
                    'metadata': backup['metadata'],
                    'integrity_verified': self.integrity_checks.get(backup_id, False)
                }
        return None

    def restore_backup(self, backup_id: str) -> bool:
        """Restaure un backup"""
        try:
            # Télécharger le backup S3
            local_path = os.path.join(self.backup_config['local_dir'], f"{backup_id}.json")
            self.s3_client.download_file(
                self.backup_config['s3_bucket'],
                f"backups/{backup_id}.json",
                local_path
            )
            
            # Vérifier l'intégrité
            if self.verify_backup_integrity(backup_id):
                # Restaurer les données
                with open(local_path, 'r') as f:
                    data = json.load(f)
                
                # Implémentation spécifique selon le type de données
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la restauration du backup {backup_id}: {e}")
            return False

    def get_backup_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques des backups"""
        total_size = sum(backup['size'] for backup in self.backup_history)
        total_count = len(self.backup_history)
        
        return {
            'total_count': total_count,
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'last_backup': self.backup_history[-1]['timestamp'] if self.backup_history else None,
            'integrity_checks': {
                'total': len(self.integrity_checks),
                'passed': sum(1 for result in self.integrity_checks.values() if result),
                'failed': sum(1 for result in self.integrity_checks.values() if not result)
            }
        }
