# Module Interface

Le module Interface fournit des interfaces utilisateur pour interagir avec Polyad. Il comprend une interface CLI et une API REST.

## Interface CLI

### Commandes Principales

```bash
# Afficher l'état
(polyad) status

# Soumettre une tâche
(polyad) task "description de la tâche"

# Voir les métriques
(polyad) monitor

# Gérer le cache
(polyad) cache

# Quitter
(polyad) quit
```

### Exemple d'utilisation

```bash
# Démarrer l'interface CLI
$ python -m polyad.interface.cli

# Afficher l'état
(polyad) status
Agent running
CPU: 25%
Memory: 45%
GPU: 15%

# Soumettre une tâche
(polyad) task "analyser l'image courante"
Task submitted with ID: 12345

# Voir les métriques
(polyad) monitor
CPU: 35%
Memory: 45%
GPU: 20%

# Quitter
(polyad) quit
```

## API REST

### Endpoints

```http
# Statut
GET /status

# Soumettre une tâche
POST /task

# Métriques
GET /metrics

# Cache
GET /cache
```

### Exemple d'utilisation

```python
import requests

# Obtenir le statut
response = requests.get("http://localhost:5000/status")
print(response.json())

# Soumettre une tâche
task = {
    "type": "system",
    "action": "monitor",
    "data": {
        "components": ["cpu", "memory", "gpu"]
    }
}
response = requests.post("http://localhost:5000/task", json=task)
print(response.json())

# Obtenir les métriques
response = requests.get("http://localhost:5000/metrics")
print(response.json())

# Obtenir les statistiques du cache
response = requests.get("http://localhost:5000/cache")
print(response.json())
```

## Meilleures pratiques

1. **Interface CLI**
   - Utiliser les commandes courtes
   - Documenter chaque commande
   - Gérer les erreurs
   - Maintenir la cohérence

2. **API REST**
   - Utiliser des endpoints clairs
   - Documenter chaque endpoint
   - Gérer les erreurs
   - Maintenir la cohérence

## Dépannage

### Problèmes courants

1. **Interface CLI**
   - Commandes inconnues
   - Entrées invalides
   - Erreurs de syntaxe
   - Problèmes de connexion

2. **API REST**
   - Endpoints inaccessibles
   - Erreurs de validation
   - Problèmes de connexion
   - Problèmes de performance

## Contribuer

Pour contribuer à ce module :

1. Lire la documentation
2. Comprendre l'architecture
3. Écrire des tests
4. Documenter les changements
5. Soumettre une Pull Request
