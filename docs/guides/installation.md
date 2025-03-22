# Guide d'Installation de Polyad

Ce guide vous aidera à installer et configurer le système d'IA autonome Polyad sur votre machine.

## Prérequis

- Python 3.9+ 
- pip (gestionnaire de paquets Python)
- Navigateur web moderne (Chrome, Firefox, Safari)
- Minimum 4 Go de RAM
- 2 Go d'espace disque disponible

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/polyad.git
cd polyad
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
```

Activation de l'environnement virtuel :

- **Windows** :
  ```bash
  venv\Scripts\activate
  ```

- **macOS/Linux** :
  ```bash
  source venv/bin/activate
  ```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

Copiez le fichier de configuration d'exemple :

```bash
cp config/config.example.json config/config.json
```

Éditez le fichier `config/config.json` pour ajuster les paramètres selon vos besoins :

```json
{
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "secret_key": "votre-clé-secrète",
    "jwt_secret": "votre-clé-jwt"
  },
  "dashboard": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "agent": {
    "data_dir": "data",
    "log_level": "info",
    "max_memory": 1024,
    "max_cpu": 80
  },
  "security": {
    "enable_auth": true,
    "default_username": "admin",
    "default_password": "changez-moi"
  }
}
```

### 5. Initialisation de la base de données

```bash
python scripts/init_db.py
```

## Démarrage

### Démarrer l'API

```bash
python run_api.py
```

L'API sera accessible à l'adresse `http://localhost:5000/api`.

### Démarrer le Dashboard

```bash
python run_dashboard.py
```

Le dashboard sera accessible à l'adresse `http://localhost:8080`.

## Vérification de l'installation

1. Ouvrez votre navigateur et accédez à `http://localhost:8080`
2. Connectez-vous avec les identifiants par défaut (ou ceux que vous avez configurés) :
   - Nom d'utilisateur : `admin`
   - Mot de passe : `changez-moi`
3. Vous devriez voir le dashboard de Polyad avec les métriques système

## Configuration avancée

### Sécurité

Pour renforcer la sécurité de votre installation :

1. Modifiez les clés secrètes dans `config.json`
2. Changez le mot de passe par défaut
3. Configurez un proxy inverse (comme Nginx) avec HTTPS
4. Limitez l'accès réseau aux ports utilisés

### Optimisation des performances

Pour améliorer les performances :

1. Ajustez les paramètres `max_memory` et `max_cpu` dans la configuration
2. Utilisez un serveur WSGI comme Gunicorn pour l'API en production
3. Activez le cache distribué pour les opérations fréquentes

### Mise à l'échelle

Pour déployer Polyad à grande échelle :

1. Configurez plusieurs instances derrière un équilibreur de charge
2. Utilisez une base de données externe pour le stockage persistant
3. Configurez un système de cache distribué comme Redis

## Dépannage

### Problèmes courants

1. **L'API ne démarre pas** :
   - Vérifiez que les ports ne sont pas déjà utilisés
   - Vérifiez les permissions des fichiers et répertoires
   - Consultez les logs dans `logs/api.log`

2. **Le dashboard ne se connecte pas à l'API** :
   - Vérifiez que l'API est bien en cours d'exécution
   - Vérifiez la configuration des CORS
   - Vérifiez les paramètres réseau et pare-feu

3. **Erreurs d'authentification** :
   - Vérifiez les identifiants dans la configuration
   - Réinitialisez le mot de passe avec `python scripts/reset_password.py`

## Support

Si vous rencontrez des problèmes lors de l'installation ou de l'utilisation de Polyad, veuillez :

1. Consulter la [documentation complète](https://docs.polyad.ai)
2. Vérifier les [problèmes connus](https://github.com/votre-utilisateur/polyad/issues)
3. Rejoindre notre [communauté Discord](https://discord.gg/polyad)
4. Contacter le support à support@polyad.ai

## Mise à jour

Pour mettre à jour Polyad vers la dernière version :

```bash
git pull
pip install -r requirements.txt
python scripts/migrate_db.py
```

## Désinstallation

Pour désinstaller Polyad :

```bash
# Arrêtez d'abord tous les services en cours d'exécution
# Puis supprimez le répertoire
cd ..
rm -rf polyad
```
