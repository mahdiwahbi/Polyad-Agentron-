from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Import des modules locaux
from api.routes import (
    agent_routes, vision_routes, audio_routes, 
    action_routes, learning_routes, system_routes
)

# Import des modules de sécurité et d'optimisation
from core.security.audit import SecurityAudit
from core.security.encryption import EncryptionManager
from core.optimization.cache import CacheManager
from core.optimization.load_balancer import LoadBalancer, BalancingStrategy

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app(testing=False):
    """
    Crée et configure l'application Flask
    
    Args:
        testing (bool): Si True, configure l'app pour les tests
        
    Returns:
        Flask: Application Flask configurée
    """
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('api.config.Config')
    
    if testing:
        app.config.from_object('api.config.TestConfig')
    
    # CORS
    CORS(app)
    
    # JWT
    jwt = JWTManager(app)
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/api/static/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Polyad API"}
    )
    
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Initialiser les composants
    app.security_audit = SecurityAudit()
    app.encryption = EncryptionManager()
    app.cache = CacheManager(implementation="redis" if not testing else "memory")
    app.load_balancer = LoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)
    
    # Enregistrer les blueprints
    app.register_blueprint(agent_routes.bp)
    app.register_blueprint(vision_routes.bp)
    app.register_blueprint(audio_routes.bp)
    app.register_blueprint(action_routes.bp)
    app.register_blueprint(learning_routes.bp)
    app.register_blueprint(system_routes.bp)
    
    @app.before_request
    def before_request():
        """Middleware exécuté avant chaque requête"""
        g.request_start_time = datetime.utcnow()
        
        # Journaliser la requête
        app.security_audit.log_access_attempt(
            username=get_jwt_identity() if get_jwt_identity() else 'anonymous',
            ip_address=request.remote_addr,
            endpoint=request.endpoint,
            method=request.method,
            user_agent=request.user_agent.string,
            status='pending'
        )
    
    @app.after_request
    def after_request(response):
        """Middleware exécuté après chaque requête"""
        # Calculer le temps de réponse
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            
            # Mettre à jour le statut de la tentative d'accès
            app.security_audit.log_access_attempt(
                username=get_jwt_identity() if get_jwt_identity() else 'anonymous',
                ip_address=request.remote_addr,
                endpoint=request.endpoint,
                method=request.method,
                user_agent=request.user_agent.string,
                status='success' if response.status_code < 400 else 'failure',
                details={
                    'status_code': response.status_code,
                    'duration': duration
                }
            )
        
        return response
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Gestionnaire pour les erreurs de rate limiting"""
        return jsonify(error="ratelimit exceeded", message=str(e.description)), 429
    
    @app.route('/api/auth/login', methods=['POST'])
    @limiter.limit("5 per minute")
    def login():
        """Endpoint d'authentification"""
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400
        
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        
        if not username or not password:
            return jsonify({"msg": "Missing username or password"}), 400
        
        # Dans une implémentation réelle, vérifier les credentials dans la base de données
        if username == "admin" and password == "password":
            access_token = create_access_token(
                identity=username,
                expires_delta=timedelta(hours=1)
            )
            return jsonify(access_token=access_token), 200
        
        app.security_audit.log_event(
            'failed_login',
            'medium',
            'authentication',
            f"Échec de connexion pour l'utilisateur {username}",
            {'ip': request.remote_addr}
        )
        
        return jsonify({"msg": "Bad username or password"}), 401
    
    @app.route('/api/health')
    def health():
        """Endpoint de vérification de santé"""
        return jsonify({
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config['VERSION']
        })
    
    @app.route('/api/system/status')
    @jwt_required()
    def system_status():
        """Endpoint de statut système"""
        # Récupérer les statistiques des différents composants
        cache_stats = app.cache.get_stats()
        lb_stats = app.load_balancer.get_stats()
        security_report = app.security_audit.generate_security_report()
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'cache': cache_stats,
                'load_balancer': lb_stats,
                'security': {
                    'vulnerabilities': len(security_report['vulnerabilities']),
                    'failed_access_attempts': security_report['summary']['failed_access_attempts'],
                    'status': 'ok' if len(security_report['vulnerabilities']) == 0 else 'warning'
                }
            }
        })
    
    return app
# Import des middlewares et autres dépendances
from api.middleware.auth import authenticate
from api.middleware.logging import setup_logging
from core.autonomous_agent import AutonomousAgent

# Point d'entrée de l'application
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
from core.resource_manager import ResourceManager
from utils.logger import logger

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'polyad-secret-key')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'polyad-jwt-secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialisation des extensions
jwt = JWTManager(app)
CORS(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration de Swagger
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Polyad API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Initialisation du logging
setup_logging(app)

# Variables globales
agent = None
resource_manager = None

# Routes d'authentification
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Authentification et génération de token JWT"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if authenticate(username, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Enregistrement des blueprints
app.register_blueprint(agent_routes.bp)
app.register_blueprint(vision_routes.bp)
app.register_blueprint(audio_routes.bp)
app.register_blueprint(action_routes.bp)
app.register_blueprint(learning_routes.bp)
app.register_blueprint(system_routes.bp)

# Route de santé
@app.route('/api/health')
def health_check():
    """Vérification de l'état de l'API"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Gestionnaire d'erreurs global
@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Erreur non gérée: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': str(e),
        'timestamp': datetime.now().isoformat()
    }), 500

async def initialize():
    """Initialisation asynchrone de l'agent et du gestionnaire de ressources"""
    global agent, resource_manager
    
    try:
        # Initialiser le gestionnaire de ressources
        resource_manager = ResourceManager()
        
        # Initialiser l'agent
        agent = AutonomousAgent()
        if not await agent.initialize():
            logger.error("Échec d'initialisation de l'agent")
            return False
            
        logger.info("Agent et gestionnaire de ressources initialisés avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur d'initialisation: {e}")
        return False

def run_app(host='0.0.0.0', port=5000, debug=False):
    """Démarrer l'application API"""
    # Initialiser de manière asynchrone
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(initialize())
    
    if not success:
        logger.error("Échec du démarrage de l'API")
        return
        
    # Démarrer Flask
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_app(debug=True)
