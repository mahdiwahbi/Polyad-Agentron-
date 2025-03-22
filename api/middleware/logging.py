"""
Middleware de logging pour l'API Polyad
"""

import logging
import os
import structlog
from flask import Flask, request, g
from datetime import datetime
import json

def setup_logging(app: Flask):
    """
    Configure le logging pour l'application
    
    Args:
        app (Flask): Application Flask
    """
    # S'assurer que le répertoire de logs existe
    os.makedirs('logs', exist_ok=True)
    
    # Configuration du logger de base
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(app.config.get('LOG_FILE', 'logs/api.log')),
            logging.StreamHandler()
        ]
    )
    
    # Configuration du logger structuré
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(indent=None)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Créer un logger structuré
    logger = structlog.get_logger('api')
    app.structlog = logger
    
    # Middleware de logging des requêtes
    @app.before_request
    def before_request_logging():
        """Log avant le traitement de la requête"""
        g.start_time = datetime.utcnow()
        
        # Logger les détails de la requête
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.user_agent.string
        )
    
    @app.after_request
    def after_request_logging(response):
        """Log après le traitement de la requête"""
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            # Logger les détails de la réponse
            logger.info(
                "request_finished",
                method=request.method,
                path=request.path,
                status=response.status_code,
                duration=duration,
                content_length=response.content_length
            )
        
        return response
    
    @app.errorhandler(Exception)
    def log_exception(error):
        """Log des exceptions non gérées"""
        logger.exception(
            "unhandled_exception",
            method=request.method,
            path=request.path,
            error=str(error)
        )
        
        # Retourner une réponse d'erreur généralisée
        return json.dumps({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    
    app.logger.info("Logging setup complete")
