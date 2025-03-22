"""
Middleware d'authentification pour l'API Polyad
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def authenticate(roles=None):
    """
    Décorateur pour authentifier et autoriser les requêtes
    
    Args:
        roles (list, optional): Liste des rôles autorisés. Par défaut None (tous les rôles)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # Vérifier le token JWT
                verify_jwt_in_request()
                
                # Récupérer l'identité de l'utilisateur
                current_user = get_jwt_identity()
                
                # Dans une implémentation réelle, vérifier les rôles de l'utilisateur
                if roles:
                    user_roles = ['admin']  # À remplacer par la récupération réelle des rôles
                    if not any(role in user_roles for role in roles):
                        current_app.security_audit.log_event(
                            'unauthorized_access',
                            'medium',
                            'authentication',
                            f"Tentative d'accès non autorisé par {current_user}",
                            {'required_roles': roles, 'user_roles': user_roles}
                        )
                        return jsonify({
                            'status': 'error',
                            'message': 'Insufficient permissions'
                        }), 403
                
                # Journaliser l'accès autorisé
                current_app.security_audit.log_event(
                    'authorized_access',
                    'info',
                    'authentication',
                    f"Accès autorisé pour {current_user}",
                    {'endpoint': request.endpoint}
                )
                
                return fn(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"Authentication error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication failed'
                }), 401
        return wrapper
    return decorator
