"""
Configuration pour l'API Polyad
"""

import os
from datetime import timedelta

class Config:
    """Configuration de base"""
    
    # Version de l'API
    VERSION = "1.0.0"
    
    # Clé secrète pour Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuration JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Configuration Redis
    REDIS_URL = os.environ.get('REDIS_URL') or "redis://localhost:6379/0"
    
    # Configuration du cache
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 3600
    
    # Configuration de la base de données
    DATABASE_URL = os.environ.get('DATABASE_URL') or "sqlite:///polyad.db"
    
    # Configuration des logs
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/api.log"
    
    # Configuration de sécurité
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'security-salt-change-in-production'
    SECURITY_AUDIT_LOG = "logs/security_audit.log"
    
    # Configuration du rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "200 per day"
    
    # Configuration des uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}
    
    # Configuration CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    
    # Configuration de l'agent autonome
    AGENT_MODEL = "gpt-4"
    AGENT_MAX_TOKENS = 2048
    AGENT_TEMPERATURE = 0.7
    
    # Configuration des timeouts
    REQUEST_TIMEOUT = 30  # secondes
    LONG_RUNNING_TIMEOUT = 300  # secondes
    
    # Configuration du load balancer
    LB_STRATEGY = "round_robin"
    LB_HEALTH_CHECK_INTERVAL = 60  # secondes
    LB_BACKEND_MAX_FAILS = 3
    
    # Configuration des métriques
    METRICS_ENABLED = True
    METRICS_INTERVAL = 60  # secondes


class TestConfig(Config):
    """Configuration pour les tests"""
    
    TESTING = True
    
    # Utiliser une base de données en mémoire pour les tests
    DATABASE_URL = "sqlite:///:memory:"
    
    # Utiliser un cache en mémoire pour les tests
    CACHE_TYPE = "simple"
    
    # Désactiver le rate limiting pour les tests
    RATELIMIT_ENABLED = False
    
    # Réduire les timeouts pour les tests
    REQUEST_TIMEOUT = 5
    LONG_RUNNING_TIMEOUT = 30
    
    # Désactiver les métriques pour les tests
    METRICS_ENABLED = False


class ProductionConfig(Config):
    """Configuration pour la production"""
    
    # Forcer l'utilisation de variables d'environnement en production
    SECRET_KEY = os.environ['SECRET_KEY']
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    SECURITY_PASSWORD_SALT = os.environ['SECURITY_PASSWORD_SALT']
    
    # Configuration de sécurité renforcée
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Configuration SSL/TLS
    SSL_REDIRECT = True
    
    # Configuration des logs
    LOG_LEVEL = "WARNING"
    
    # Configuration CORS plus restrictive
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Configuration du rate limiting plus stricte
    RATELIMIT_DEFAULT = "100 per day"
    
    # Configuration des métriques
    METRICS_ENABLED = True
    METRICS_INTERVAL = 30  # secondes
