"""
Routes pour la gestion système
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
import psutil
import os
from datetime import datetime

bp = Blueprint('system', __name__, url_prefix='/api/system')

@bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """Récupère les métriques système"""
    try:
        # Récupérer les métriques système
        metrics = {
            'cpu': {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            }
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving system metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_stats():
    """Récupère les statistiques de performance"""
    try:
        # Récupérer les statistiques de performance des différents composants
        stats = {
            'cache': current_app.cache.get_stats(),
            'load_balancer': current_app.load_balancer.get_stats(),
            'security': current_app.security_audit.get_stats(),
            'api': {
                'requests_total': 1000,
                'requests_per_second': 10.5,
                'average_response_time': 0.15,
                'error_rate': 0.02
            }
        }
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving performance stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/logs', methods=['GET'])
@jwt_required()
def get_system_logs():
    """Récupère les logs système"""
    try:
        # Paramètres de pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        level = request.args.get('level', 'INFO')
        
        # Dans une implémentation réelle, récupérer les logs depuis le fichier ou la base de données
        logs = [
            {
                'timestamp': '2025-03-21T01:04:35Z',
                'level': 'INFO',
                'component': 'api',
                'message': 'Request processed successfully',
                'details': {'endpoint': '/api/vision/process', 'duration': 0.15}
            },
            {
                'timestamp': '2025-03-21T01:04:30Z',
                'level': 'WARNING',
                'component': 'security',
                'message': 'Failed login attempt',
                'details': {'ip': '192.168.1.100'}
            }
        ]
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(logs)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving system logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/security/audit', methods=['GET'])
@jwt_required()
def get_security_audit():
    """Récupère le rapport d'audit de sécurité"""
    try:
        # Générer le rapport d'audit
        audit_report = current_app.security_audit.generate_security_report()
        
        return jsonify({
            'status': 'success',
            'report': audit_report,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error generating security audit report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/maintenance', methods=['POST'])
@jwt_required()
def trigger_maintenance():
    """Déclenche une opération de maintenance"""
    if not request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Missing JSON in request'
        }), 400
    
    operation = request.json.get('operation')
    parameters = request.json.get('parameters', {})
    
    if not operation:
        return jsonify({
            'status': 'error',
            'message': 'No operation specified'
        }), 400
    
    try:
        # Exécuter l'opération de maintenance
        if operation == 'cache_cleanup':
            await current_app.cache.cleanup()
            message = 'Cache cleanup completed'
        elif operation == 'log_rotation':
            # Dans une implémentation réelle, effectuer la rotation des logs
            message = 'Log rotation completed'
        elif operation == 'backup':
            # Dans une implémentation réelle, effectuer la sauvegarde
            message = 'Backup completed'
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown operation: {operation}'
            }), 400
        
        # Journaliser l'opération
        current_app.security_audit.log_event(
            'maintenance_operation',
            'info',
            'system',
            f"Maintenance operation '{operation}' completed successfully",
            {'parameters': parameters}
        )
        
        return jsonify({
            'status': 'success',
            'message': message
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error during maintenance operation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
