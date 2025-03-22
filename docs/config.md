# Module Configuration

Le module Configuration gère tous les aspects de la configuration de Polyad. Il est conçu pour être flexible, extensible et facile à utiliser.

## Structure de la Configuration

La configuration est organisée en plusieurs sections principales :

```yaml
# Configuration générale
polyad:
  debug: false
  log_level: "INFO"
  
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

# Configuration de monitoring
monitoring:
  grafana:
    api_key: null
    host: "localhost"
    port: 3000
  metrics_interval: 1
  alert_thresholds:
    cpu: 90
    memory: 90
    temperature: 80
```

## Classes Principales

### Config

```python
class Config:
    """
    Gestionnaire de configuration
    
    Args:
        config_file (str): Chemin du fichier de configuration
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialise la configuration
        
        Args:
            config_file (str): Chemin du fichier de configuration
        """
    
    def get(self, key: str) -> Any:
        """
        Obtient une valeur de configuration
        
        Args:
            key (str): Clé de configuration
            
        Returns:
            Any: Valeur de configuration
        """
    
    def set(self, key: str, value: Any) -> None:
        """
        Définit une valeur de configuration
        
        Args:
            key (str): Clé de configuration
            value (Any): Nouvelle valeur
        """
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Met à jour la configuration
        
        Args:
            updates (Dict[str, Any]): Mises à jour de configuration
        """
    
    def reload(self) -> None:
        """
        Recharge la configuration
        """
    
    def validate(self) -> bool:
        """
        Valide la configuration
        
        Returns:
            bool: True si la configuration est valide
        """
```

## Validation

La configuration est validée automatiquement :

```python
def validate_config(config: Dict[str, Any]) -> bool:
    """
    Valide la configuration
    
    Args:
        config (Dict[str, Any]): Configuration à valider
        
    Returns:
        bool: True si la configuration est valide
    """
    
    # Vérifier les champs requis
    required_fields = [
        'cache',
        'gpu',
        'security',
        'monitoring'
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Configuration manquante: {field}")
            
    # Vérifier les valeurs
    if config['cache']['size'] <= 0:
        raise ValueError("Taille du cache invalide")
        
    if config['cache']['ttl'] <= 0:
        raise ValueError("TTL du cache invalide")
        
    if config['gpu']['memory_threshold'] < 0 or config['gpu']['memory_threshold'] > 1:
        raise ValueError("Seuil mémoire GPU invalide")
        
    if config['gpu']['temperature_threshold'] < 0:
        raise ValueError("Seuil température GPU invalide")
        
    return True
```

## Utilisation

### Chargement de la Configuration

```python
from polyad.config import Config

# Charger la configuration
config = Config()

# Obtenir une valeur
cache_size = config.get('cache.size')

# Mettre à jour une valeur
config.set('cache.size', 2 * 1024 * 1024 * 1024)  # 2GB

# Mettre à jour plusieurs valeurs
config.update({
    'cache.ttl': 7200,  # 2 heures
    'gpu.memory_threshold': 0.9
})

# Recharger la configuration
config.reload()
```

### Validation

```python
# Valider la configuration
if not config.validate():
    raise ValueError("Configuration invalide")
```

## Meilleures pratiques

1. Toujours valider la configuration
2. Utiliser des valeurs par défaut raisonnables
3. Documenter chaque paramètre
4. Gérer les erreurs de configuration
5. Maintenir la cohérence

## Dépannage

### Problèmes courants

1. **Validation**
   - Vérifier les champs requis
   - Vérifier les valeurs
   - Vérifier les types

2. **Configuration**
   - Vérifier les chemins
   - Vérifier les permissions
   - Vérifier les formats

3. **Performance**
   - Optimiser la validation
   - Utiliser le cache
   - Minimiser les rechargements

## Contribuer

Pour contribuer à ce module :

1. Lire la documentation
2. Comprendre l'architecture
3. Écrire des tests
4. Documenter les changements
5. Soumettre une Pull Request
