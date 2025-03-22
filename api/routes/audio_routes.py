"""
Routes pour le traitement audio
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
import os

bp = Blueprint('audio', __name__, url_prefix='/api/audio')

@bp.route('/process', methods=['POST'])
@jwt_required()
def process_audio():
    """Traite un fichier audio"""
    if 'audio' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No audio file provided'
        }), 400
    
    file = request.files['audio']
    
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
    
    if file and file.filename.split('.')[-1].lower() in {'mp3', 'wav'}:
        try:
            # Sauvegarder le fichier audio
            filename = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            
            # Dans une implémentation réelle, traiter l'audio ici
            
            return jsonify({
                'status': 'success',
                'message': 'Audio processed successfully',
                'filename': file.filename
            }), 200
        except Exception as e:
            current_app.logger.error(f"Error processing audio: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'File type not allowed'
        }), 400

@bp.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe_audio():
    """Transcrit un fichier audio"""
    if 'audio' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No audio file provided'
        }), 400
    
    file = request.files['audio']
    
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
    
    if file and file.filename.split('.')[-1].lower() in {'mp3', 'wav'}:
        try:
            # Dans une implémentation réelle, transcrire l'audio ici
            transcription = {
                'text': 'Hello, this is a sample transcription',
                'confidence': 0.95,
                'duration': 10.5,
                'language': 'en'
            }
            
            return jsonify({
                'status': 'success',
                'transcription': transcription
            }), 200
        except Exception as e:
            current_app.logger.error(f"Error transcribing audio: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'File type not allowed'
        }), 400
