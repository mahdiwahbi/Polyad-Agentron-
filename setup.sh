#!/bin/bash

# Afficher un message de bienvenue
echo "Installation de Polyad - Agent IA Général Autonome"
echo "Configuration pour MacBook 2019 avec macOS Ventura+"

# Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    echo "Installation de Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Ajouter Homebrew au PATH si nécessaire
    if [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
fi

# Install system dependencies
echo "Installation des dépendances système..."
brew install ollama
brew install python@3.11
brew install portaudio
brew install ffmpeg
brew install sqlite

# Optimisations pour macOS
echo "Configuration des optimisations pour macOS Ventura..."
defaults write NSGlobalDomain NSAppSleepDisabled -bool true

# Install Python dependencies
echo "Installation des dépendances Python..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Pull Ollama models
echo "Téléchargement des modèles Ollama..."
ollama pull gemma3:12b-q4_0
ollama pull gemma3:12b-q2_K

# Setup Metal support
echo "Configuration du support Metal pour GPU..."
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu

# Create necessary directories
echo "Création des répertoires nécessaires..."
mkdir -p ~/Desktop/MAI/polyad/cache
mkdir -p ~/Desktop/MAI/polyad/data
mkdir -p ~/Desktop/MAI/polyad/logs

# Configuration des permissions
echo "Configuration des permissions..."
chmod +x ~/Desktop/MAI/polyad/*.py
chmod +x ~/Desktop/MAI/polyad/examples/*.py
chmod +x ~/Desktop/MAI/polyad/tests/*.py

# Création du fichier de configuration par défaut
echo "Création du fichier de configuration par défaut..."
if [ ! -f ~/Desktop/MAI/polyad/config.json ]; then
    cp ~/Desktop/MAI/polyad/config.json.example ~/Desktop/MAI/polyad/config.json 2>/dev/null || echo "Fichier de configuration exemple non trouvé, utilisation de la configuration par défaut"
fi

# Optimisation du système
echo "Optimisation du système pour de meilleures performances..."
if [ "$EUID" -eq 0 ]; then
    echo "Désactivation du swap pour améliorer les performances..."
    launchctl unload -w /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist 2>/dev/null || echo "Impossible de désactiver le swap, continuez en mode normal"
    
    echo "Nettoyage de la mémoire..."
    purge
else
    echo "Pour des performances optimales, exécutez ce script en tant que root (sudo) pour désactiver le swap"
fi

# Vérification de l'installation
echo "Vérification de l'installation..."
python3 -c "import langchain, psutil, cv2, speech_recognition, pyautogui, faiss; print('Toutes les dépendances sont correctement installées')" || echo "Certaines dépendances n'ont pas été installées correctement"

# Vérification des modèles Ollama
echo "Vérification des modèles Ollama..."
ollama list | grep -q "gemma3:12b" && echo "Modèles Gemma3 correctement installés" || echo "Les modèles Gemma3 n'ont pas été correctement installés"

# Finalisation
echo "Installation terminée!"
echo "Pour démarrer Polyad, exécutez: python3 ~/Desktop/MAI/polyad/polyad.py --task \"Votre tâche ici\""
echo "Pour des exemples d'utilisation, consultez le répertoire examples/"
