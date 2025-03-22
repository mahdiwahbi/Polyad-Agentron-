#!/bin/bash

# Script de déploiement pour Polyad
# Auteur: Polyad Team
# Date: 2023

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher un message d'en-tête
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

# Fonction pour afficher un message de section
print_section() {
    echo -e "\n${YELLOW}---------------------------------------------------${NC}"
    echo -e "${YELLOW} $1 ${NC}"
    echo -e "${YELLOW}---------------------------------------------------${NC}"
}

# Fonction pour afficher un message de succès
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Fonction pour afficher un message d'erreur
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour afficher un message d'information
print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Vérifier que le script est exécuté depuis le bon répertoire
if [ ! -f "polyad.py" ]; then
    print_error "Ce script doit être exécuté depuis le répertoire racine de Polyad."
    exit 1
fi

# Vérifier les permissions d'exécution
if [ ! -x "setup.sh" ]; then
    print_info "Ajout des permissions d'exécution à setup.sh"
    chmod +x setup.sh
fi

if [ ! -x "run_tests.sh" ]; then
    print_info "Ajout des permissions d'exécution à run_tests.sh"
    chmod +x run_tests.sh
fi

# Vérifier l'installation
print_header "VÉRIFICATION DE L'INSTALLATION"

./run_tests.sh

if [ $? -ne 0 ]; then
    print_error "La vérification de l'installation a échoué. Veuillez corriger les erreurs avant de continuer."
    exit 1
fi

# Options de déploiement
print_header "OPTIONS DE DÉPLOIEMENT"

print_section "SÉLECTION DU MODE DE DÉPLOIEMENT"
echo "1. Déploiement local (service utilisateur)"
echo "2. Déploiement système (service système)"
echo "3. Déploiement conteneur (Docker)"
echo "4. Déploiement API (serveur web)"
echo "5. Quitter"

read -p "Sélectionnez une option (1-5): " -n 1 -r
echo
case $REPLY in
    1)
        # Déploiement local
        print_section "DÉPLOIEMENT LOCAL"
        
        # Créer le répertoire de service utilisateur
        SERVICE_DIR="$HOME/.config/systemd/user"
        mkdir -p "$SERVICE_DIR"
        
        # Créer le fichier de service
        SERVICE_FILE="$SERVICE_DIR/polyad.service"
        POLYAD_DIR="$(pwd)"
        
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Polyad AI Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $POLYAD_DIR/polyad.py
WorkingDirectory=$POLYAD_DIR
Restart=on-failure
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF
        
        print_info "Fichier de service créé: $SERVICE_FILE"
        
        # Recharger les services utilisateur
        systemctl --user daemon-reload
        
        # Activer et démarrer le service
        print_info "Activation du service Polyad..."
        systemctl --user enable polyad.service
        
        print_info "Démarrage du service Polyad..."
        systemctl --user start polyad.service
        
        # Vérifier l'état du service
        sleep 2
        systemctl --user status polyad.service
        
        print_success "Polyad a été déployé en tant que service utilisateur."
        print_info "Pour vérifier l'état: systemctl --user status polyad.service"
        print_info "Pour arrêter: systemctl --user stop polyad.service"
        print_info "Pour désactiver: systemctl --user disable polyad.service"
        ;;
        
    2)
        # Déploiement système
        print_section "DÉPLOIEMENT SYSTÈME"
        
        # Vérifier les privilèges sudo
        if [ "$EUID" -ne 0 ]; then
            print_error "Le déploiement système nécessite des privilèges sudo."
            print_info "Veuillez exécuter: sudo ./deploy.sh"
            exit 1
        fi
        
        # Créer le fichier de service système
        SERVICE_FILE="/etc/systemd/system/polyad.service"
        POLYAD_DIR="$(pwd)"
        
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Polyad AI Agent
After=network.target

[Service]
Type=simple
User=$(logname)
Group=$(id -gn $(logname))
ExecStart=/usr/bin/python3 $POLYAD_DIR/polyad.py
WorkingDirectory=$POLYAD_DIR
Restart=on-failure
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
        
        print_info "Fichier de service créé: $SERVICE_FILE"
        
        # Recharger les services système
        systemctl daemon-reload
        
        # Activer et démarrer le service
        print_info "Activation du service Polyad..."
        systemctl enable polyad.service
        
        print_info "Démarrage du service Polyad..."
        systemctl start polyad.service
        
        # Vérifier l'état du service
        sleep 2
        systemctl status polyad.service
        
        print_success "Polyad a été déployé en tant que service système."
        print_info "Pour vérifier l'état: sudo systemctl status polyad.service"
        print_info "Pour arrêter: sudo systemctl stop polyad.service"
        print_info "Pour désactiver: sudo systemctl disable polyad.service"
        ;;
        
    3)
        # Déploiement Docker
        print_section "DÉPLOIEMENT DOCKER"
        
        # Vérifier si Docker est installé
        if ! command -v docker &> /dev/null; then
            print_error "Docker n'est pas installé."
            print_info "Veuillez installer Docker: https://docs.docker.com/get-docker/"
            exit 1
        fi
        
        # Créer le Dockerfile s'il n'existe pas
        if [ ! -f "Dockerfile" ]; then
            print_info "Création du Dockerfile..."
            
            cat > "Dockerfile" << EOF
FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Installer Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copier les fichiers du projet
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Créer les répertoires nécessaires
RUN mkdir -p logs cache

# Exposer le port (si nécessaire)
# EXPOSE 8080

# Commande par défaut
CMD ["python", "polyad.py"]
EOF
            
            print_success "Dockerfile créé."
        else
            print_info "Dockerfile existant détecté."
        fi
        
        # Construire l'image Docker
        print_info "Construction de l'image Docker..."
        docker build -t polyad:latest .
        
        if [ $? -eq 0 ]; then
            print_success "Image Docker construite avec succès."
            
            # Exécuter le conteneur
            print_info "Exécution du conteneur Polyad..."
            docker run -d --name polyad polyad:latest
            
            if [ $? -eq 0 ]; then
                print_success "Conteneur Polyad démarré avec succès."
                print_info "Pour voir les logs: docker logs polyad"
                print_info "Pour arrêter le conteneur: docker stop polyad"
                print_info "Pour supprimer le conteneur: docker rm polyad"
            else
                print_error "Erreur lors du démarrage du conteneur."
            fi
        else
            print_error "Erreur lors de la construction de l'image Docker."
        fi
        ;;
        
    4)
        # Déploiement API
        print_section "DÉPLOIEMENT API"
        
        # Vérifier si Flask est installé
        if ! pip3 show flask &> /dev/null; then
            print_info "Installation de Flask..."
            pip3 install flask gunicorn
        fi
        
        # Créer le fichier API s'il n'existe pas
        API_FILE="api.py"
        if [ ! -f "$API_FILE" ]; then
            print_info "Création du fichier API..."
            
            cat > "$API_FILE" << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from flask import Flask, request, jsonify
from polyad import Polyad

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'api.log')),
        logging.StreamHandler()
    ]
)

# Initialiser l'application Flask
app = Flask(__name__)

# Initialiser Polyad
polyad = Polyad()

@app.route('/api/run', methods=['POST'])
def run_task():
    """Point d'entrée principal pour exécuter une tâche"""
    try:
        # Récupérer les données de la requête
        data = request.json
        
        if not data or 'task' not in data:
            return jsonify({
                'success': False,
                'error': 'La tâche est requise'
            }), 400
        
        # Exécuter la tâche
        task = data['task']
        result = polyad.run(task)
        
        # Retourner le résultat
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la tâche: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retourne les statistiques de performance"""
    try:
        stats = polyad.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des statistiques: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifie l'état de santé de l'API"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0'
    })

# Point d'entrée pour l'exécution directe
if __name__ == '__main__':
    # Créer le répertoire de logs s'il n'existe pas
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Démarrer le serveur
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
            
            print_success "Fichier API créé: $API_FILE"
            
            # Rendre le fichier exécutable
            chmod +x "$API_FILE"
        else
            print_info "Fichier API existant détecté: $API_FILE"
        fi
        
        # Créer le script de démarrage
        START_SCRIPT="start_api.sh"
        if [ ! -f "$START_SCRIPT" ]; then
            print_info "Création du script de démarrage..."
            
            cat > "$START_SCRIPT" << EOF
#!/bin/bash
# Script de démarrage de l'API Polyad

# Vérifier si Gunicorn est installé
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn n'est pas installé. Installation..."
    pip3 install gunicorn
fi

# Démarrer l'API avec Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 api:app
EOF
            
            print_success "Script de démarrage créé: $START_SCRIPT"
            
            # Rendre le script exécutable
            chmod +x "$START_SCRIPT"
        else
            print_info "Script de démarrage existant détecté: $START_SCRIPT"
        fi
        
        # Démarrer l'API
        print_info "Démarrage de l'API Polyad..."
        print_info "L'API sera accessible à l'adresse: http://localhost:5000"
        print_info "Pour arrêter l'API, appuyez sur Ctrl+C"
        
        # Exécuter le script de démarrage
        ./$START_SCRIPT
        ;;
        
    5)
        print_info "Déploiement annulé."
        exit 0
        ;;
        
    *)
        print_error "Option invalide."
        exit 1
        ;;
esac

print_header "DÉPLOIEMENT TERMINÉ"
print_success "Polyad a été déployé avec succès."

exit 0
