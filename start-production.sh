#!/bin/bash
# Script de démarrage pour l'environnement de production Polyad

set -e

echo "=== Démarrage de Polyad en mode production ==="

# Vérification des dépendances
echo "Vérification de l'installation de Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker n'est pas installé. Veuillez installer Docker pour continuer."
    exit 1
fi

echo "Vérification de l'installation de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose n'est pas installé. Veuillez installer Docker Compose pour continuer."
    exit 1
fi

# Vérification de Ollama
echo "Vérification d'Ollama..."
if ! curl -s --head  --request GET http://localhost:11434/api/version | grep "200" > /dev/null; then
    echo "Ollama n'est pas démarré ou n'est pas accessible. Veuillez démarrer Ollama."
    exit 1
fi

# Vérification du modèle
echo "Vérification du modèle gemma3:12b-it-q4_K_M..."
if ! curl -s "http://localhost:11434/api/tags" | grep -q "gemma3:12b-it-q4_K_M"; then
    echo "Le modèle gemma3:12b-it-q4_K_M n'est pas disponible. Veuillez le télécharger avec 'ollama pull gemma3:12b-it-q4_K_M'."
    exit 1
fi

# Création des répertoires nécessaires
mkdir -p data logs backups

# Chargement des variables d'environnement
if [ -f .env.production ]; then
    echo "Chargement des variables d'environnement depuis .env.production..."
    export $(grep -v '^#' .env.production | xargs)
fi

# Construction et démarrage des conteneurs
echo "Construction et démarrage des conteneurs Docker..."
docker-compose down --remove-orphans
docker-compose build
docker-compose up -d

echo "Attente du démarrage des services..."
sleep 10

# Vérification de l'état des services
echo "Vérification de l'état des services..."
if ! docker-compose ps | grep "polyad" | grep "Up" > /dev/null; then
    echo "Le service Polyad n'a pas démarré correctement. Consultez les logs pour plus d'informations."
    docker-compose logs polyad
    exit 1
fi

# Affichage des URLs de service
echo ""
echo "=== Polyad a démarré avec succès ! ==="
echo "- API: http://localhost:8000"
echo "- Dashboard: http://localhost:8001"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo ""
echo "Pour consulter les logs: docker-compose logs -f"
echo "Pour arrêter les services: docker-compose down"
echo ""
