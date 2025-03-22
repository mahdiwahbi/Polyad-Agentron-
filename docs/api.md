# Module API

Le module API fournit une interface REST pour interagir avec Polyad. Il est conçu pour être sécurisé, scalable et facile à utiliser.

## Endpoints

### 1. Statut de l'Agent

```http
GET /status
```

**Description** : Obtient le statut actuel de l'agent

**Réponse** :
```json
{
    "status": "running",
    "uptime": "1h 30m",
    "resources": {
        "cpu": 25,
        "memory": 45,
        "gpu": 15
    },
    "cache": {
        "size": "1.2GB",
        "hits": 12345,
        "misses": 123
    }
}
```

### 2. Soumission de Tâches

```http
POST /task
```

**Description** : Soumet une nouvelle tâche à l'agent

**Paramètres** :
```json
{
    "type": "string",      // Type de tâche (system, vision, audio, etc.)
    "action": "string",    // Action spécifique
    "data": {},           // Données de la tâche
    "priority": "normal"  // Priorité (low, normal, high)
}
```

**Réponse** :
```json
{
    "task_id": "12345",
    "status": "accepted",
    "estimated_time": "2m 30s"
}
```

### 3. Métriques Système

```http
GET /metrics
```

**Description** : Obtient les métriques système en temps réel

**Réponse** :
```json
{
    "cpu": {
        "usage": 35,
        "temperature": 55
    },
    "memory": {
        "usage": 45,
        "available": "8GB"
    },
    "gpu": {
        "usage": 20,
        "temperature": 65
    },
    "network": {
        "upload": "1Mbps",
        "download": "10Mbps"
    }
}
```

### 4. Statistiques du Cache

```http
GET /cache
```

**Description** : Obtient les statistiques du cache

**Réponse** :
```json
{
    "size": "1.2GB",
    "hits": 12345,
    "misses": 123,
    "hit_rate": 98.5,
    "evictions": 10,
    "last_cleanup": "2024-03-21T07:50:00"
}
```

## Sécurité

1. **Authentification**
   - JWT pour l'authentification
   - Rate limiting pour la sécurité
   - CORS pour les requêtes

2. **Validation**
   - Validation des entrées
   - Protection contre les injections
   - Validation des types

3. **Gestion des erreurs**
   - Gestion sécurisée des erreurs
   - Logging sécurisé
   - Validation des types

## Performance

1. **Cache**
   - Cache en mémoire
   - Cache Redis
   - Cache LRU

2. **Optimisation**
   - Gestion de la mémoire
   - Optimisation CPU
   - Optimisation GPU

## Monitoring

1. **Métriques**
   - CPU
   - Mémoire
   - GPU
   - Température
   - Réseau

2. **Alertes**
   - Seuils configurables
   - Notifications
   - Logs détaillés

## Utilisation

### Initialisation

```python
from polyad.api.app import create_app

# Créer l'application
app = create_app()

# Démarrer le serveur
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
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

1. Toujours utiliser l'authentification
2. Limiter le nombre de requêtes
3. Utiliser le cache pour les données fréquemment utilisées
4. Surveiller les métriques pour détecter les problèmes
5. Gérer les erreurs de manière appropriée

## Dépannage

### Problèmes courants

1. **Performance**
   - Vérifier les métriques système
   - Ajuster la configuration du cache
   - Optimiser les requêtes

2. **Sécurité**
   - Vérifier les tokens JWT
   - Valider les entrées
   - Surveiller les logs

3. **Cache**
   - Vérifier l'utilisation de la mémoire
   - Ajuster le TTL
   - Nettoyer le cache

## Contribuer

Pour contribuer à ce module :

1. Lire la documentation
2. Comprendre l'architecture
3. Écrire des tests
4. Documenter les changements
5. Soumettre une Pull Request
