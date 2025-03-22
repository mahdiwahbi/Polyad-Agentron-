import pytest
import os
import json
from datetime import datetime, timedelta
from core.backup_manager import BackupManager
from utils.logger import logger

@pytest.fixture
def backup_manager():
    config = {
        'backup': {
            'local_dir': 'test_backup',
            's3_bucket': 'test-bucket',
            'retention_days': 7,
            'cleanup_interval': 3600,
            'compression_level': 9,
            'encryption_key': 'test-key',
            'verify_integrity': True
        }
    }
    
    # Créer le répertoire de test
    os.makedirs('test_backup', exist_ok=True)
    
    return BackupManager(config)

@pytest.fixture
def test_data():
    return {
        'test_key': 'test_value',
        'timestamp': datetime.now().isoformat(),
        'metadata': {
            'user': 'test_user',
            'version': '1.0.0'
        }
    }

def test_create_backup(backup_manager, test_data):
    """Test la création d'un backup"""
    backup_id = backup_manager.create_backup(test_data, test_data['metadata'])
    
    assert backup_id.startswith('backup_')
    assert os.path.exists(os.path.join('test_backup', f"{backup_id}.json"))
    assert os.path.exists(os.path.join('test_backup', f"{backup_id}_metadata.json"))

def test_backup_integrity(backup_manager, test_data):
    """Test la vérification d'intégrité d'un backup"""
    backup_id = backup_manager.create_backup(test_data, test_data['metadata'])
    
    # Vérifier l'intégrité
    assert backup_manager.verify_backup_integrity(backup_id)
    
    # Modifier le fichier et vérifier l'intégrité
    backup_path = os.path.join('test_backup', f"{backup_id}.json")
    with open(backup_path, 'r') as f:
        data = json.load(f)
    data['test_key'] = 'modified_value'
    
    with open(backup_path, 'w') as f:
        json.dump(data, f)
    
    assert not backup_manager.verify_backup_integrity(backup_id)

def test_backup_cleanup(backup_manager, test_data):
    """Test le nettoyage des backups anciens"""
    # Créer plusieurs backups
    for i in range(5):
        backup_manager.create_backup(test_data, test_data['metadata'])
    
    # Modifier la date de modification d'un fichier pour le rendre ancien
    old_backup = os.listdir('test_backup')[0]
    old_path = os.path.join('test_backup', old_backup)
    os.utime(old_path, (datetime.now() - timedelta(days=8)).timestamp())
    
    # Nettoyer les backups
    backup_manager._cleanup_old_backups()
    
    # Vérifier que le backup ancien a été supprimé
    assert not os.path.exists(old_path)

def test_restore_backup(backup_manager, test_data):
    """Test la restauration d'un backup"""
    backup_id = backup_manager.create_backup(test_data, test_data['metadata'])
    
    # Restaurer le backup
    assert backup_manager.restore_backup(backup_id)
    
    # Vérifier que les données ont été restaurées correctement
    backup_path = os.path.join('test_backup', f"{backup_id}.json")
    with open(backup_path, 'r') as f:
        restored_data = json.load(f)
    
    assert restored_data == test_data

def test_backup_statistics(backup_manager, test_data):
    """Test les statistiques des backups"""
    # Créer plusieurs backups
    for i in range(3):
        backup_manager.create_backup(test_data, test_data['metadata'])
    
    # Obtenir les statistiques
    stats = backup_manager.get_backup_statistics()
    
    assert stats['total_count'] == 3
    assert stats['total_size_gb'] > 0
    assert stats['last_backup'] is not None
    assert stats['integrity_checks']['total'] == 3
    assert stats['integrity_checks']['passed'] == 3

@pytest.fixture
def cleanup_test_backup():
    """Nettoie le répertoire de test après les tests"""
    yield
    if os.path.exists('test_backup'):
        shutil.rmtree('test_backup')

@pytest.fixture(autouse=True)
def run_around_tests(cleanup_test_backup):
    """Exécute les tests avec le nettoyage automatique"""
    yield
