# Module Core

Le module Core contient les composants essentiels du système Polyad. Il est organisé en plusieurs sous-modules :

## Sous-modules

### Agent

Le composant Agent (`agent.py`) est le cœur du système :

```python
class PolyadAgent:
    """
    Agent principal de Polyad
    
    Gère l'initialisation, le démarrage et l'arrêt des services
    Fournit des méthodes pour traiter les requêtes
    
    Args:
        config (Config): Configuration de l'agent
    """
    
    async def initialize(self) -> bool:
        """
        Initialise l'agent
        
        Returns:
            bool: True si l'initialisation a réussi
        """
    
    async def start(self) -> None:
        """
        Démarre l'agent
        """
    
    async def stop(self) -> None:
        """
        Arrête l'agent proprement
        """
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une requête
        
        Args:
            request (Dict[str, Any]): Requête à traiter
            
        Returns:
            Dict[str, Any]: Résultat du traitement
        """
```

### Cache

Le système de cache (`cache_manager.py`) est conçu pour optimiser les performances :

```python
class CacheManager:
    """
    Gestionnaire de cache multi-niveau
    
    Utilise un système de cache en mémoire, Redis et LRU
    
    Args:
        config (Dict[str, Any]): Configuration du cache
    """
    
    async def get(self, key: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Obtient une valeur du cache
        
        Args:
            key (str): Clé du cache
            
        Returns:
            Optional[Union[str, Dict[str, Any]]]: Valeur du cache ou None
        """
    
    async def set(self, key: str, value: Union[str, Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """
        Définit une valeur dans le cache
        
        Args:
            key (str): Clé du cache
            value (Union[str, Dict[str, Any]]): Valeur à stocker
            ttl (Optional[int]): Temps de vie en secondes
            
        Returns:
            bool: True si l'opération a réussi
        """
```

### Optimisation

Le module d'optimisation (`gpu_optimizer.py`) gère les performances du système :

```python
class GPUOptimizer:
    """
    Optimiseur GPU
    
    Gère l'optimisation de la mémoire, de la température et de la charge GPU
    
    Args:
        config (Dict[str, Any]): Configuration de l'optimiseur
    """
    
    async def initialize(self) -> bool:
        """
        Initialise l'optimiseur GPU
        
        Returns:
            bool: True si l'initialisation a réussi
        """
    
    async def start(self) -> None:
        """
        Démarre la surveillance et l'optimisation GPU
        """
    
    async def stop(self) -> None:
        """
        Arrête la surveillance et l'optimisation GPU
        """
```

### Sécurité

Le module de sécurité (`encryption.py`) protège les données sensibles :

```python
class EncryptionManager:
    """
    Gestionnaire de chiffrement
    
    Utilise AES-256 et RSA-2048 pour la sécurité
    
    Args:
        key (Optional[str]): Clé de chiffrement
        salt (Optional[bytes]): Sel pour la dérivation de clé
    """
    
    def encrypt(self, data: str) -> str:
        """
        Chiffre les données
        
        Args:
            data (str): Données à chiffrer
            
        Returns:
            str: Données chiffrées encodées en base64
        """
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Déchiffre les données
        
        Args:
            encrypted_data (str): Données chiffrées encodées en base64
            
        Returns:
            str: Données déchiffrées
        """
```

### Monitoring

Le module de monitoring (`monitoring.py`) surveille les performances du système :

```python
class MonitoringService:
    """
    Service de monitoring
    
    Utilise Prometheus et Grafana pour le monitoring
    
    Args:
        config (Dict[str, Any]): Configuration du monitoring
    """
    
    async def initialize(self) -> bool:
        """
        Initialise le service de monitoring
        
        Returns:
            bool: True si l'initialisation a réussi
        """
    
    async def start(self) -> None:
        """
        Démarre la surveillance
        """
    
    async def stop(self) -> None:
        """
        Arrête la surveillance
        """
```

## Configuration

Chaque composant peut être configuré via le fichier `config.yaml` :

```yaml
# Configuration du cache
cache:
  size: 1024 * 1024 * 1024  # 1GB
  ttl: 3600                  # 1 heure
  cleanup_interval: 300      # 5 minutes
  redis:
    host: "localhost"
    port: 6379
    db: 0

# Configuration GPU
gpu:
  memory_threshold: 0.8
  temperature_threshold: 80
  optimization_interval: 60  # secondes

# Configuration de sécurité
security:
  encryption_key: null
  salt: null
  iterations: 100000
```

## Utilisation

### Initialisation

```python
from polyad.core.agent import PolyadAgent
from polyad.core.cache import CacheManager
from polyad.core.optimization import GPUOptimizer
from polyad.core.security import EncryptionManager
from polyad.core.monitoring import MonitoringService

# Initialiser les composants
agent = PolyadAgent(config)
cache = CacheManager(config)
optimizer = GPUOptimizer(config)
encryption = EncryptionManager(config)
monitoring = MonitoringService(config)

# Démarrer les services
await agent.start()
await cache.start()
await optimizer.start()
await encryption.initialize()
await monitoring.start()
```

### Traitement d'une requête

```python
# Chiffrer les données sensibles
data = encryption.encrypt("données sensibles")

# Stocker dans le cache
await cache.set("key", data)

# Traiter la requête
result = await agent.process_request({
    "type": "system",
    "action": "monitor",
    "components": ["cpu", "memory", "gpu"]
})

# Surveiller les performances
metrics = monitoring.get_metrics()
```

## Meilleures pratiques

1. Toujours chiffrer les données sensibles
2. Utiliser le cache pour les données fréquemment utilisées
3. Surveiller les métriques pour détecter les problèmes
4. Configurer les seuils d'alerte appropriés
5. Nettoyer régulièrement le cache

## Dépannage

### Problèmes courants

1. **Performance GPU**
   - Vérifier la température
   - Ajuster les seuils de mémoire
   - Optimiser la charge

2. **Cache**
   - Vérifier l'utilisation de la mémoire
   - Ajuster le TTL
   - Nettoyer le cache

3. **Sécurité**
   - Vérifier les clés de chiffrement
   - Valider les entrées
   - Surveiller les logs

## Contribuer

Pour contribuer à ce module :

1. Lire la documentation
2. Comprendre l'architecture
3. Écrire des tests
4. Documenter les changements
5. Soumettre une Pull Request
