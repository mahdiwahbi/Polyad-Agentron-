#!/bin/bash
# Script de lancement pour l'application Polyad

# Définition des chemins
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Fonction de nettoyage à la sortie
cleanup() {
    echo "Arrêt des services Polyad..."
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        docker-compose down
    else
        # Trouver et arrêter les processus
        pkill -f "python.*main.py"
    fi
    exit 0
}

# Capture des signaux pour arrêter proprement
trap cleanup EXIT INT TERM

# Vérification des dépendances
if ! command -v docker &> /dev/null; then
    osascript -e 'display notification "Docker n'\'est pas installé" with title "Erreur Polyad"'
    osascript -e 'display dialog "Docker n'\'est pas installé sur votre système. Veuillez installer Docker pour continuer." buttons {"OK"} default button "OK" with icon stop with title "Erreur Polyad"'
    exit 1
fi

if ! docker info &> /dev/null; then
    osascript -e 'display notification "Docker n'\'est pas démarré" with title "Erreur Polyad"'
    osascript -e 'display dialog "Docker n'\'est pas démarré. Veuillez démarrer Docker et réessayer." buttons {"OK"} default button "OK" with icon stop with title "Erreur Polyad"'
    exit 1
fi

# Vérification d'Ollama
if ! curl -s --head --request GET http://localhost:11434/api/version | grep "200" > /dev/null; then
    osascript -e 'display notification "Ollama n'\'est pas accessible" with title "Erreur Polyad"'
    osascript -e 'display dialog "Ollama n'\'est pas démarré ou n'\'est pas accessible. Veuillez démarrer Ollama et réessayer." buttons {"OK"} default button "OK" with icon stop with title "Erreur Polyad"'
    exit 1
fi

# Notification de démarrage
osascript -e 'display notification "Démarrage des services..." with title "Polyad"'

# Chargement des variables d'environnement
if [ -f "$SCRIPT_DIR/.env.production" ]; then
    source "$SCRIPT_DIR/.env.production"
fi

# Lancement des services
echo "Démarrage de Polyad..."
if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    # Mode production avec Docker
    docker-compose down --remove-orphans
    docker-compose up -d
    
    # Vérification du démarrage
    sleep 5
    if ! docker-compose ps | grep "polyad" | grep "Up" > /dev/null; then
        osascript -e 'display notification "Échec du démarrage des services" with title "Erreur Polyad"'
        docker-compose logs polyad
        exit 1
    fi
    
    # Notification de succès
    osascript -e 'display notification "Services démarrés avec succès !" with title "Polyad"'
    
    # Ouverture automatique des interfaces
    sleep 2
    open "http://localhost:8001" # Dashboard
    
    # Affichage des URLs
    echo "=== Polyad a démarré avec succès ! ==="
    echo "- API: http://localhost:8000"
    echo "- Dashboard: http://localhost:8001"
    echo "- Prometheus: http://localhost:9090"
    echo "- Grafana: http://localhost:3000"
    
    # Maintenir le script en cours d'exécution
    echo "Appuyez sur Ctrl+C pour arrêter Polyad..."
    tail -f /dev/null
else
    # Mode développement sans Docker
    python main.py &
    MAIN_PID=$!
    
    # Attente que le serveur soit prêt
    sleep 3
    if ! ps -p $MAIN_PID > /dev/null; then
        osascript -e 'display notification "Échec du démarrage de Polyad" with title "Erreur Polyad"'
        exit 1
    fi
    
    # Notification de succès
    osascript -e 'display notification "Polyad démarré avec succès !" with title "Polyad"'
    
    # Ouverture automatique des interfaces
    open "http://localhost:8001" # Dashboard
    
    # Maintenir le script en cours d'exécution
    wait $MAIN_PID
fi
