import pytest
import os
from polyad.utils.config import load_config
from polyad.core.agent import PolyadAgent
from polyad.services.cache import CacheManager
from polyad.services.model import ModelManager
from polyad.services.monitoring import MonitoringService

def setup_test_environment():
    """Configure l'environnement de test"""
    os.environ["DEBUG"] = "True"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["TEST_MODE"] = "True"
    
    # Configuration de test
    test_config = {
        "cache_size": 1 * 1024 * 1024 * 1024,  # 1GB pour les tests
        "batch_size": 2,
        "parallel_workers": 2,
        "max_queue_size": 10
    }
    
    return test_config

@pytest.fixture
def test_config():
    return setup_test_environment()

@pytest.fixture
def agent(test_config):
    """Crée une instance de l'agent pour les tests"""
    config = load_config()
    cache_manager = CacheManager(config)
    model_manager = ModelManager(config)
    monitoring_service = MonitoringService(config)
    
    agent = PolyadAgent(
        config=config,
        cache_manager=cache_manager,
        model_manager=model_manager,
        monitoring_service=monitoring_service
    )
    
    yield agent
    
    # Nettoyage après les tests
    agent.stop()
    cache_manager.stop()
    model_manager.stop()
    monitoring_service.stop()

@pytest.fixture
def metrics_service(test_config):
    """Crée une instance du service de métriques pour les tests"""
    from polyad.monitoring.metrics import Metrics
    return Metrics()

@pytest.fixture
def backup_manager(test_config):
    """Crée une instance du gestionnaire de backup pour les tests"""
    from polyad.core.backup import BackupManager
    return BackupManager(test_config)

@pytest.fixture
def auth_service(test_config):
    """Crée une instance du service d'authentification pour les tests"""
    from polyad.security.auth import oauth2_scheme
    return oauth2_scheme

@pytest.fixture
def attack_protection(test_config):
    """Crée une instance de la protection contre les attaques pour les tests"""
    from polyad.security.attack_protection import AttackProtection
    return AttackProtection(test_config)

@pytest.fixture
def audit_logger(test_config):
    """Crée une instance du journalier d'audit pour les tests"""
    from polyad.security.audit_logger import AuditLogger
    return AuditLogger(test_config)

@pytest.fixture
def compression_manager(test_config):
    """Crée une instance du gestionnaire de compression pour les tests"""
    from polyad.utils.compression import CompressionManager
    return CompressionManager(test_config)

@pytest.fixture
def notification_manager(test_config):
    """Crée une instance du gestionnaire de notifications pour les tests"""
    from polyad.notifications.notification_manager import NotificationManager
    return NotificationManager(test_config)

@pytest.fixture
def rate_limiter(test_config):
    """Crée une instance du gestionnaire de débit pour les tests"""
    from polyad.utils.rate_limiter import RateLimiter
    return RateLimiter(test_config)

@pytest.fixture
def dlq_manager(test_config):
    """Crée une instance du gestionnaire de la dead letter queue pour les tests"""
    from polyad.utils.dlq_manager import DLQManager
    return DLQManager(test_config)

def test_agent_initialization(agent):
    """Vérifie que l'agent s'initialise correctement"""
    assert agent is not None
    assert agent.config is not None
    assert agent.cache_manager is not None
    assert agent.model_manager is not None
    assert agent.monitoring_service is not None

def test_cache_operations(agent):
    """Teste les opérations de cache"""
    data = {"test_key": "test_value"}
    agent.cache_manager.set("test_key", data)
    
    result = agent.cache_manager.get("test_key")
    assert result == data
    
    agent.cache_manager.delete("test_key")
    assert agent.cache_manager.get("test_key") is None

def test_model_processing(agent):
    """Teste le traitement du modèle"""
    prompt = "Quelle est la capitale de la France?"
    
    response = agent.model_manager.generate(prompt)
    assert "Paris" in response["text"]
    
    # Vérifier les métriques
    metrics = agent.monitoring_service.get_metrics()
    assert metrics["model_calls"] > 0
    assert metrics["cache_hits"] >= 0

def test_performance_monitoring(agent):
    """Teste le monitoring des performances"""
    initial_metrics = agent.monitoring_service.get_metrics()
    
    # Simuler une charge
    for _ in range(5):
        prompt = "Test performance monitoring"
        agent.model_manager.generate(prompt)
    
    final_metrics = agent.monitoring_service.get_metrics()
    
    assert final_metrics["model_calls"] > initial_metrics["model_calls"]
    assert final_metrics["cache_hits"] >= initial_metrics["cache_hits"]
    assert final_metrics["memory_usage"] > 0
    assert final_metrics["cpu_usage"] > 0

def test_resource_management(agent):
    """Teste la gestion des ressources"""
    # Vérifier les seuils de ressources
    assert agent.config["cpu_threshold"] == 80
    assert agent.config["gpu_threshold"] == 70
    assert agent.config["memory_threshold"] == 0.8
    
    # Simuler une surcharge
    agent.monitoring_service.simulate_high_cpu_usage()
    
    # Vérifier la réaction
    assert agent.monitoring_service.check_resource_limits()
    
    # Réinitialiser
    agent.monitoring_service.reset_simulation()

def test_security_token_generation(auth_service):
    """Teste la génération et la validation des tokens"""
    from polyad.security.auth import create_access_token, verify_token
    
    # Créer un token
    token = create_access_token(data={"sub": "test_user"})
    assert token is not None
    
    # Valider le token
    username = verify_token(token)
    assert username == "test_user"

def test_metrics_collection(metrics_service):
    """Teste la collecte des métriques"""
    # Enregistrer une requête
    metrics_service.record_request()
    
    # Enregistrer une erreur
    metrics_service.record_error("test_error")
    
    # Enregistrer un temps de réponse
    metrics_service.record_response_time(0.5)
    
    # Vérifier les métriques
    assert metrics_service.request_counter._value.get() > 0
    assert metrics_service.error_counter._metrics[('test_error',)]._value.get() > 0
    
    # Vérifier les histogrammes
    assert len(metrics_service.response_time._buckets) > 0

def test_backup_system(backup_manager, tmp_path):
    """Teste le système de backup"""
    # Créer un dossier de test
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    
    # Créer un fichier de test
    test_file = test_dir / "test.txt"
    test_file.write_text("Test data")
    
    # Créer un backup
    backup_path = backup_manager.create_backup(str(test_dir))
    assert os.path.exists(backup_path)
    
    # Vérifier le contenu du backup
    backup_dir = os.path.dirname(backup_path)
    extracted_dir = tmp_path / "extracted"
    extracted_dir.mkdir()
    
    import tarfile
    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(path=str(extracted_dir))
    
    extracted_file = extracted_dir / "test.txt"
    assert extracted_file.exists()
    assert extracted_file.read_text() == "Test data"
    
    # Nettoyer les backups anciens
    backup_manager.cleanup_old_backups()
    
    # Vérifier que le backup a été supprimé
    assert not os.path.exists(backup_path)

def test_monitoring_alerts(agent):
    """Teste les alertes de monitoring"""
    # Simuler une surcharge CPU
    agent.monitoring_service.simulate_high_cpu_usage()
    
    # Vérifier les alertes
    alerts = agent.monitoring_service.get_alerts()
    assert len(alerts) > 0
    
    # Vérifier les types d'alertes
    alert_types = [alert["type"] for alert in alerts]
    assert "cpu_high" in alert_types
    
    # Réinitialiser
    agent.monitoring_service.reset_simulation()
    
    # Vérifier que les alertes ont été réinitialisées
    alerts = agent.monitoring_service.get_alerts()
    assert len(alerts) == 0

def test_rate_limiting(attack_protection):
    """Teste la limitation de taux"""
    client_id = "test_client"
    
    # Tester sous la limite
    for _ in range(999):
        assert attack_protection.check_rate_limit(client_id)
    
    # Tester à la limite
    assert attack_protection.check_rate_limit(client_id)
    
    # Tester au-delà de la limite
    assert not attack_protection.check_rate_limit(client_id)

def test_ip_blocklist(attack_protection):
    """Teste la liste noire des IP"""
    ip_address = "192.168.1.1"
    
    # Tester une IP non bloquée
    assert attack_protection.check_ip_blocklist(ip_address)
    
    # Bloquer l'IP
    attack_protection._block_client(ip_address)
    
    # Tester une IP bloquée
    assert not attack_protection.check_ip_blocklist(ip_address)

def test_ddos_protection(attack_protection):
    """Teste la protection contre les attaques DDoS"""
    # Tester sous le seuil
    assert attack_protection.check_ddos(9999)
    
    # Tester au-dessus du seuil
    assert not attack_protection.check_ddos(10001)

def test_sql_injection_protection(attack_protection):
    """Teste la protection contre les injections SQL"""
    # Tester une entrée valide
    assert attack_protection.check_sql_injection("select * from users")
    
    # Tester une injection SQL
    assert not attack_protection.check_sql_injection("DROP TABLE users; --")

def test_xss_protection(attack_protection):
    """Teste la protection contre les attaques XSS"""
    # Tester une entrée valide
    assert attack_protection.check_xss("<p>Test</p>")
    
    # Tester une attaque XSS
    assert not attack_protection.check_xss("<script>alert('XSS')</script>")

def test_audit_logging(audit_logger):
    """Teste la journalisation des audits"""
    user_id = "test_user"
    event_type = "login"
    details = {"success": True}
    
    # Enregistrer un événement
    audit_logger.log_event(event_type, user_id, details)
    
    # Vérifier l'historique
    history = audit_logger.get_audit_history(user_id=user_id)
    assert len(history) == 1
    assert history[0]["event_type"] == event_type

def test_audit_statistics(audit_logger):
    """Teste les statistiques d'audit"""
    # Enregistrer plusieurs événements
    for i in range(3):
        audit_logger.log_event("login", f"user_{i}", {"success": True})
    
    # Vérifier les statistiques
    stats = audit_logger.get_audit_statistics()
    assert stats["total_logs"] == 3
    assert stats["categories"]["authentication"] == 3

def test_data_compression(compression_manager):
    """Teste la compression des données"""
    test_data = "Test data to compress" * 1000
    
    # Compresser avec différentes méthodes
    for method in ["zlib", "bz2", "lzma"]:
        compressed = compression_manager.compress_data(test_data, method)
        assert len(compressed) < len(test_data)
        
        # Décompresser et vérifier
        decompressed = compression_manager.decompress_data(compressed, method)
        assert decompressed.decode("utf-8") == test_data

def test_file_compression(compression_manager, tmp_path):
    """Teste la compression des fichiers"""
    # Créer un fichier de test
    test_file = tmp_path / "test.txt"
    test_data = "Test data to compress" * 1000
    test_file.write_text(test_data)
    
    # Compresser le fichier
    compressed_file = tmp_path / "test.compressed"
    compression_manager.compress_file(str(test_file), str(compressed_file))
    
    # Vérifier la taille
    assert compressed_file.stat().st_size < test_file.stat().st_size
    
    # Décompresser et vérifier
    decompressed_file = tmp_path / "test.decompressed"
    compression_manager.decompress_file(str(compressed_file), str(decompressed_file))
    assert decompressed_file.read_text() == test_data

def test_notification_sending(notification_manager):
    """Teste l'envoi des notifications"""
    user_id = "test_user"
    title = "Test Notification"
    message = "This is a test notification"
    
    # Envoyer une notification
    notification = notification_manager.send_notification(
        user_id,
        title,
        message,
        priority="high",
        providers=["email", "slack", "mobile"]
    )
    
    # Vérifier l'historique
    history = notification_manager.get_notification_history(user_id=user_id)
    assert len(history) == 1
    assert history[0]["title"] == title

def test_notification_statistics(notification_manager):
    """Teste les statistiques des notifications"""
    # Envoyer plusieurs notifications
    for i in range(3):
        notification_manager.send_notification(
            f"user_{i}",
            "Test",
            "Test message",
            priority="medium"
        )
    
    # Vérifier les statistiques
    stats = notification_manager.get_notification_statistics()
    assert stats["total_sent"] == 3
    assert stats["by_priority"]["medium"] == 3

def test_advanced_rate_limiting(rate_limiter):
    """Teste le rate limiting avancé"""
    client_id = "test_client"
    
    # Tester la limite de base
    for _ in range(999):
        assert rate_limiter.check_rate_limit(client_id)
    
    # Tester la limite avec burst
    for _ in range(100):
        assert rate_limiter.check_rate_limit(client_id, burst=True)
    
    # Tester au-delà de la limite
    assert not rate_limiter.check_rate_limit(client_id)

def test_rate_limiting_with_ip(rate_limiter):
    """Teste le rate limiting avec IP"""
    ip_address = "192.168.1.1"
    
    # Tester la limite par IP
    for _ in range(999):
        assert rate_limiter.check_rate_limit(ip_address)
    
    # Tester au-delà de la limite
    assert not rate_limiter.check_rate_limit(ip_address)

def test_dead_letter_queue(dlq_manager):
    """Teste la dead letter queue"""
    message = {"id": "test", "data": "test data"}
    
    # Envoyer un message dans la DLQ
    dlq_manager.send_to_dlq(message)
    
    # Vérifier la récupération
    recovered = dlq_manager.get_from_dlq()
    assert recovered == message

def test_dlq_cleanup(dlq_manager):
    """Teste le nettoyage de la DLQ"""
    # Envoyer plusieurs messages
    for i in range(10):
        dlq_manager.send_to_dlq({"id": f"test_{i}", "data": f"test data {i}"})
    
    # Nettoyer les messages anciens
    dlq_manager.cleanup_old_messages()
    
    # Vérifier le nombre de messages restants
    messages = dlq_manager.get_all_messages()
    assert len(messages) <= dlq_manager.config["max_messages"]
