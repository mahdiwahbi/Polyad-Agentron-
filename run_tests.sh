#!/bin/bash

# Script pour exécuter les tests et vérifier l'installation de Polyad
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

# Fonction pour vérifier si une commande existe
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "La commande '$1' n'est pas installée."
        return 1
    else
        print_success "La commande '$1' est installée."
        return 0
    fi
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

# Créer les répertoires nécessaires s'ils n'existent pas
if [ ! -d "logs" ]; then
    print_info "Création du répertoire logs"
    mkdir -p logs
fi

if [ ! -d "cache" ]; then
    print_info "Création du répertoire cache"
    mkdir -p cache
fi

if [ ! -d "examples" ]; then
    print_info "Création du répertoire examples"
    mkdir -p examples
fi

# Vérifier si config.json existe, sinon le créer à partir de l'exemple
if [ ! -f "config.json" ] && [ -f "config.json.example" ]; then
    print_info "Création de config.json à partir de l'exemple"
    cp config.json.example config.json
fi

# Vérifier les dépendances système
print_header "VÉRIFICATION DES DÉPENDANCES SYSTÈME"

check_command python3
check_command pip3
check_command ollama

# Vérifier l'installation de Python
print_section "VÉRIFICATION DE PYTHON"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    print_success "Python $PYTHON_VERSION est installé (version 3.8+ requise)."
else
    print_error "Python $PYTHON_VERSION est installé, mais la version 3.8+ est requise."
    exit 1
fi

# Vérifier les dépendances Python
print_section "VÉRIFICATION DES DÉPENDANCES PYTHON"

if [ -f "requirements.txt" ]; then
    print_info "Vérification des dépendances à partir de requirements.txt"
    
    # Vérifier si les dépendances sont installées
    MISSING_DEPS=$(pip3 freeze | grep -v "^\-e" | cut -d= -f1 | sort | comm -23 <(sort requirements.txt) -)
    
    if [ -n "$MISSING_DEPS" ]; then
        print_error "Certaines dépendances sont manquantes:"
        echo "$MISSING_DEPS"
        
        read -p "Voulez-vous installer les dépendances manquantes? (o/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            print_info "Installation des dépendances..."
            pip3 install -r requirements.txt
            
            if [ $? -eq 0 ]; then
                print_success "Dépendances installées avec succès."
            else
                print_error "Erreur lors de l'installation des dépendances."
                exit 1
            fi
        else
            print_info "Installation des dépendances ignorée."
        fi
    else
        print_success "Toutes les dépendances sont installées."
    fi
else
    print_error "Le fichier requirements.txt est manquant."
    exit 1
fi

# Vérifier l'installation d'Ollama
print_section "VÉRIFICATION D'OLLAMA"

OLLAMA_VERSION=$(ollama version 2>&1)
if [ $? -eq 0 ]; then
    print_success "Ollama est installé: $OLLAMA_VERSION"
    
    # Vérifier les modèles disponibles
    print_info "Modèles Ollama disponibles:"
    ollama list
    
    # Vérifier si les modèles requis sont disponibles
    if ! ollama list | grep -q "gemma"; then
        print_info "Aucun modèle Gemma détecté. Il est recommandé d'installer au moins un modèle Gemma."
        read -p "Voulez-vous télécharger le modèle gemma3:2b-q2_K? (o/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            print_info "Téléchargement du modèle gemma3:2b-q2_K..."
            ollama pull gemma3:2b-q2_K
            
            if [ $? -eq 0 ]; then
                print_success "Modèle téléchargé avec succès."
            else
                print_error "Erreur lors du téléchargement du modèle."
            fi
        else
            print_info "Téléchargement du modèle ignoré."
        fi
    fi
else
    print_error "Ollama n'est pas correctement installé."
    print_info "Veuillez installer Ollama: https://ollama.ai/download"
    exit 1
fi

# Exécuter le script de vérification Python
print_header "VÉRIFICATION DE L'INSTALLATION POLYAD"

python3 check_installation.py

if [ $? -eq 0 ]; then
    print_success "La vérification de l'installation a réussi."
else
    print_error "La vérification de l'installation a échoué."
    exit 1
fi

# Exécuter les tests
print_header "EXÉCUTION DES TESTS"

read -p "Voulez-vous exécuter les tests Polyad? (o/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    print_info "Exécution des tests..."
    
    # Test du gestionnaire de ressources
    print_section "TEST DU GESTIONNAIRE DE RESSOURCES"
    python3 test_polyad.py --component resource
    
    # Test des outils
    print_section "TEST DES OUTILS"
    python3 test_polyad.py --component tools
    
    # Test des outils asynchrones
    print_section "TEST DES OUTILS ASYNCHRONES"
    python3 test_polyad.py --component async
    
    # Test de Polyad complet
    print_section "TEST DE POLYAD COMPLET"
    python3 test_polyad.py --component polyad
    
    print_success "Tests terminés."
else
    print_info "Tests ignorés."
fi

# Exécuter un exemple
print_header "EXÉCUTION D'UN EXEMPLE"

read -p "Voulez-vous exécuter un exemple Polyad? (o/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    print_info "Exemples disponibles:"
    echo "1. Exemple de base (polyad_example.py)"
    echo "2. Exemple d'outils asynchrones (async_example.py)"
    echo "3. Exemple de gestionnaire de ressources (resource_manager_example.py)"
    echo "4. Exemple d'outils (tools_example.py)"
    
    read -p "Choisissez un exemple à exécuter (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            print_info "Exécution de l'exemple de base..."
            python3 examples/polyad_example.py
            ;;
        2)
            print_info "Exécution de l'exemple d'outils asynchrones..."
            python3 examples/async_example.py
            ;;
        3)
            print_info "Exécution de l'exemple de gestionnaire de ressources..."
            python3 examples/resource_manager_example.py
            ;;
        4)
            print_info "Exécution de l'exemple d'outils..."
            python3 examples/tools_example.py
            ;;
        *)
            print_error "Choix invalide."
            ;;
    esac
else
    print_info "Exécution d'exemple ignorée."
fi

print_header "TERMINÉ"
print_success "Tous les tests et vérifications sont terminés."
print_info "Polyad est prêt à être utilisé."
print_info "Pour démarrer Polyad, exécutez: python3 polyad.py --task 'votre tâche'"

exit 0
