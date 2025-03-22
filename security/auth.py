from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import jwt
import datetime
from typing import Dict, Any, Optional
import secrets
import hashlib
from functools import wraps
from flask import request, jsonify, current_app
import logging
from utils.logger import logger

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ROLES = {
    'admin': 3,
    'manager': 2,
    'user': 1,
    'guest': 0
}

class AuthManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.auth')
        self.secret_key = config.get('jwt_secret', secrets.token_hex(32))
        self.expiration = config.get('jwt_expiration', 3600)  # 1 heure par défaut
        self.refresh_expiration = config.get('jwt_refresh_expiration', 86400)  # 24 heures par défaut
        
        # Configuration MFA
        self.mfa_enabled = config.get('mfa_enabled', True)
        self.mfa_methods = config.get('mfa_methods', ['totp', 'sms'])
        
        # Configuration des rôles
        self.role_hierarchy = {
            'admin': ['manager', 'user', 'guest'],
            'manager': ['user', 'guest'],
            'user': ['guest'],
            'guest': []
        }

    def create_jwt(self, user_id: str, role: str, mfa_verified: bool = False) -> Dict[str, str]:
        """Crée un token JWT avec les informations d'authentification"""
        payload = {
            'user_id': user_id,
            'role': role,
            'mfa_verified': mfa_verified,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.expiration)
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Créer un token de rafraîchissement
        refresh_payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.refresh_expiration)
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifie la validité d'un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token JWT expiré")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Token JWT invalide")
            return None

    def verify_mfa(self, user_id: str, code: str) -> bool:
        """Vérifie le code MFA pour un utilisateur"""
        if not self.mfa_enabled:
            return True
            
        # Implémentation spécifique selon la méthode MFA
        return True  # À implémenter

    def check_role(self, current_role: str, required_role: str) -> bool:
        """Vérifie si le rôle actuel est autorisé à accéder à la ressource"""
        if current_role == required_role:
            return True
            
        if current_role in self.role_hierarchy:
            return required_role in self.role_hierarchy[current_role]
            
        return False

    def password_policy(self, password: str) -> Dict[str, Any]:
        """Vérifie la conformité d'un mot de passe aux politiques de sécurité"""
        requirements = {
            'min_length': 12,
            'max_length': 64,
            'requires_uppercase': True,
            'requires_lowercase': True,
            'requires_digits': True,
            'requires_special': True,
            'no_repeated_chars': True,
            'no_consecutive_chars': True
        }
        
        results = {
            'valid': True,
            'requirements': {}
        }
        
        # Vérifier la longueur
        if len(password) < requirements['min_length']:
            results['valid'] = False
            results['requirements']['min_length'] = requirements['min_length']
        
        if len(password) > requirements['max_length']:
            results['valid'] = False
            results['requirements']['max_length'] = requirements['max_length']
        
        # Vérifier les caractères requis
        if requirements['requires_uppercase'] and not any(c.isupper() for c in password):
            results['valid'] = False
            results['requirements']['requires_uppercase'] = True
        
        if requirements['requires_lowercase'] and not any(c.islower() for c in password):
            results['valid'] = False
            results['requirements']['requires_lowercase'] = True
        
        if requirements['requires_digits'] and not any(c.isdigit() for c in password):
            results['valid'] = False
            results['requirements']['requires_digits'] = True
        
        if requirements['requires_special'] and not any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for c in password):
            results['valid'] = False
            results['requirements']['requires_special'] = True
        
        # Vérifier les caractères répétés
        if requirements['no_repeated_chars']:
            for i in range(len(password) - 1):
                if password[i] == password[i + 1]:
                    results['valid'] = False
                    results['requirements']['no_repeated_chars'] = True
                    break
        
        # Vérifier les caractères consécutifs
        if requirements['no_consecutive_chars']:
            for i in range(len(password) - 2):
                if ord(password[i]) + 1 == ord(password[i + 1]) and ord(password[i + 1]) + 1 == ord(password[i + 2]):
                    results['valid'] = False
                    results['requirements']['no_consecutive_chars'] = True
                    break
        
        return results

    def hash_password(self, password: str) -> str:
        """Hache un mot de passe avec un sel unique"""
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()}"

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Vérifie un mot de passe haché"""
        if not stored_password or not provided_password:
            return False
            
        salt, hash_ = stored_password.split('$')
        return hash_ == hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000).hex()

def require_role(required_role: str):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            auth_manager = current_app.auth_manager
            
            if not token:
                return jsonify({'error': 'Token manquant'}), 401
                
            payload = auth_manager.verify_jwt(token)
            if not payload:
                return jsonify({'error': 'Token invalide'}), 401
                
            if not auth_manager.check_role(payload['role'], required_role):
                return jsonify({'error': 'Accès non autorisé'}), 403
                
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def require_mfa(f):
    """Décorateur pour vérifier la vérification MFA"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        auth_manager = current_app.auth_manager
        
        if not token:
            return jsonify({'error': 'Token manquant'}), 401
            
        payload = auth_manager.verify_jwt(token)
        if not payload:
            return jsonify({'error': 'Token invalide'}), 401
            
        if not payload.get('mfa_verified', False):
            return jsonify({'error': 'Vérification MFA requise'}), 401
            
        return f(*args, **kwargs)
    
    return decorated_function

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)
