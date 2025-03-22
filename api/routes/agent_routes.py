"""
Routes pour la gestion de l'agent autonome
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from core.autonomous_agent import AutonomousAgent

bp = Blueprint('agent', __name__, url_prefix='/api/agent')

@bp.route('/start', methods=['POST'])
@jwt_required()
def start_agent():
    """Démarre l'agent autonome"""
    try:
        # Initialiser l'agent avec la configuration
        agent = AutonomousAgent(
            model=current_app.config['AGENT_MODEL'],
            max_tokens=current_app.config['AGENT_MAX_TOKENS'],
            temperature=current_app.config['AGENT_TEMPERATURE']
        )
        
        # Démarrer l'agent
        agent.initialize()
        
        return jsonify({
            'status': 'success',
            'message': 'Agent started successfully'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error starting agent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_agent():
    """Arrête l'agent autonome"""
    try:
        # Dans une implémentation réelle, arrêter l'agent ici
        return jsonify({
            'status': 'success',
            'message': 'Agent stopped successfully'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error stopping agent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/status', methods=['GET'])
@jwt_required()
def agent_status():
    """Récupère le statut de l'agent"""
    try:
        # Dans une implémentation réelle, récupérer le vrai statut
        status = {
            'status': 'running',
            'uptime': '1h 23m',
            'tasks_completed': 42,
            'tasks_pending': 7
        }
        return jsonify(status), 200
    except Exception as e:
        current_app.logger.error(f"Error getting agent status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
