import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from polyad.utils.config import load_config
from polyad.core.agent import PolyadAgent
from polyad.services.cache import CacheManager
from polyad.services.model import ModelManager
from polyad.services.monitoring import MonitoringService

# Configuration de base pour les tests
def pytest_configure(config):
    """Configuration globale pour les tests"""
    os.environ["TEST_MODE"] = "True"
    os.environ["DEBUG"] = "True"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Configuration des chemins
    config.test_dir = Path(__file__).parent
    config.data_dir = config.test_dir.parent / "data"

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Configuration de test avec types et validation"""
    config = load_config()
    
    # Configuration spécifique aux tests
    config["cache_size"] = 1 * 1024 * 1024 * 1024  # 1GB pour les tests
    config["batch_size"] = 2
    config["parallel_workers"] = 2
    config["max_queue_size"] = 10
    
    # Validation des valeurs
    assert config["cache_size"] > 0
    assert config["batch_size"] > 0
    assert config["parallel_workers"] > 0
    assert config["max_queue_size"] > 0
    
    return config

@pytest.fixture(scope="session")
def cache_manager(test_config: Dict[str, Any]) -> CacheManager:
    """Cache Manager pour les tests"""
    manager = CacheManager(test_config)
    yield manager
    manager.shutdown()

@pytest.fixture(scope="session")
def model_manager(test_config: Dict[str, Any]) -> ModelManager:
    """Model Manager pour les tests"""
    manager = ModelManager(test_config)
    yield manager
    manager.shutdown()

@pytest.fixture(scope="session")
def monitoring_service(test_config: Dict[str, Any]) -> MonitoringService:
    """Monitoring Service pour les tests"""
    service = MonitoringService(test_config)
    yield service
    service.shutdown()

@pytest.fixture(scope="session")
def test_agent(
    test_config: Dict[str, Any],
    cache_manager: CacheManager,
    model_manager: ModelManager,
    monitoring_service: MonitoringService
) -> PolyadAgent:
    """Agent pour les tests"""
    agent = PolyadAgent(
        config=test_config,
        cache_manager=cache_manager,
        model_manager=model_manager,
        monitoring_service=monitoring_service
    )
    yield agent
    agent.shutdown()
