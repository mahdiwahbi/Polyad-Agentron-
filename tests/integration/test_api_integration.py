import pytest
import json
import os
import sys
from flask import Flask
from flask.testing import FlaskClient
import jwt
from datetime import datetime, timedelta

# Ajouter le répertoire parent au chemin pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.app import create_app

@pytest.fixture
def app():
    """Créer une instance de l'application Flask pour les tests"""
    app = create_app(testing=True)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Créer un client de test pour l'application Flask"""
    return app.test_client()

@pytest.fixture
def auth_token(app):
    """Générer un token JWT valide pour les tests"""
    with app.app_context():
        expires = datetime.utcnow() + timedelta(hours=1)
        token = jwt.encode(
            {'sub': 'test-user', 'exp': expires},
            app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        return token

def test_health_endpoint(client):
    """Tester l'endpoint de santé de l'API"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'online'
    assert 'version' in data
    assert 'timestamp' in data

def test_login_endpoint(client):
    """Tester l'endpoint de login"""
    # Données de test
    credentials = {
        'username': 'admin',
        'password': 'password'
    }
    
    # Envoyer la requête
    response = client.post(
        '/api/auth/login',
        data=json.dumps(credentials),
        content_type='application/json'
    )
    
    # Vérifier la réponse
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    
    # Vérifier que le token est valide
    token = data['access_token']
    decoded = jwt.decode(
        token,
        'test-secret-key',  # Utiliser la même clé que dans l'application
        algorithms=['HS256'],
        options={"verify_signature": True}
    )
    assert 'sub' in decoded
    assert 'exp' in decoded

def test_protected_endpoint_without_token(client):
    """Tester un endpoint protégé sans token"""
    response = client.get('/api/system/status')
    assert response.status_code == 401

def test_protected_endpoint_with_token(client, auth_token):
    """Tester un endpoint protégé avec token"""
    response = client.get(
        '/api/system/status',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'system' in data

def test_rate_limiting(client):
    """Tester le rate limiting"""
    # Envoyer plusieurs requêtes en succession rapide
    for _ in range(10):
        client.get('/api/health')
    
    # La requête suivante devrait être limitée
    response = client.get('/api/health')
    assert response.status_code == 429

def test_agent_start_stop(client, auth_token):
    """Tester le démarrage et l'arrêt de l'agent"""
    # Démarrer l'agent
    start_response = client.post(
        '/api/agent/start',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert start_response.status_code == 200
    start_data = json.loads(start_response.data)
    assert start_data['status'] == 'success'
    
    # Arrêter l'agent
    stop_response = client.post(
        '/api/agent/stop',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert stop_response.status_code == 200
    stop_data = json.loads(stop_response.data)
    assert stop_data['status'] == 'success'

def test_vision_processing(client, auth_token):
    """Tester le traitement de vision"""
    # Créer une image de test
    with open('tests/fixtures/test_image.jpg', 'rb') as f:
        image_data = f.read()
    
    # Envoyer l'image pour traitement
    response = client.post(
        '/api/vision/process',
        data={
            'image': (image_data, 'test_image.jpg')
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'result' in data
    assert 'items' in data['result']

def test_audio_processing(client, auth_token):
    """Tester le traitement audio"""
    # Créer un fichier audio de test
    with open('tests/fixtures/test_audio.wav', 'rb') as f:
        audio_data = f.read()
    
    # Envoyer l'audio pour traitement
    response = client.post(
        '/api/audio/process',
        data={
            'audio': (audio_data, 'test_audio.wav')
        },
        headers={'Authorization': f'Bearer {auth_token}'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'result' in data
    assert 'transcription' in data['result']
