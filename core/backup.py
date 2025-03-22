import os
import shutil
import time
from datetime import datetime
from typing import Dict, Optional
import boto3
from botocore.exceptions import NoCredentialsError

class BackupManager:
    def __init__(self, config: Dict):
        self.config = config
        self.backup_dir = config.get('backup', {}).get('directory', 'backups')
        self.backup_interval = config.get('backup', {}).get('interval', 24)  # hours
        self.backup_retention = config.get('backup', {}).get('retention', 7)  # days
        self.s3_bucket = config.get('backup', {}).get('s3_bucket')
        self.s3_region = config.get('backup', {}).get('s3_region')
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, source_dir: str) -> str:
        """Create a new backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}.tar.gz'
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            shutil.make_archive(
                os.path.splitext(backup_path)[0],
                'gztar',
                source_dir
            )
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to create backup: {str(e)}")
    
    def upload_to_s3(self, backup_path: str) -> bool:
        """Upload backup to S3 if configured"""
        if not self.s3_bucket or not self.s3_region:
            return False
            
        try:
            s3 = boto3.client('s3', region_name=self.s3_region)
            s3.upload_file(
                backup_path,
                self.s3_bucket,
                os.path.basename(backup_path)
            )
            return True
        except NoCredentialsError:
            raise Exception("AWS credentials not found")
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    def cleanup_old_backups(self) -> None:
        """Remove backups older than retention period"""
        now = datetime.now()
        for backup in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, backup)
            if os.path.isfile(backup_path):
                backup_time = datetime.fromtimestamp(os.path.getctime(backup_path))
                if (now - backup_time).days > self.backup_retention:
                    os.remove(backup_path)
    
    def run_backup(self, source_dir: str) -> None:
        """Run complete backup process"""
        try:
            backup_path = self.create_backup(source_dir)
            if self.s3_bucket:
                self.upload_to_s3(backup_path)
            self.cleanup_old_backups()
        except Exception as e:
            raise Exception(f"Backup failed: {str(e)}")
    
    def schedule_backups(self) -> None:
        """Schedule periodic backups"""
        while True:
            try:
                self.run_backup(self.config.get('data_directory', '.'))
                time.sleep(self.backup_interval * 3600)  # Convert hours to seconds
            except Exception as e:
                print(f"Error during backup: {str(e)}")
                time.sleep(3600)  # Wait an hour before retrying
