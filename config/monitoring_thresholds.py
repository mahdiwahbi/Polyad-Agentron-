# Seuils de monitoring pour Polyad

# Ressources
RESOURCE_THRESHOLDS = {
    'cpu': {
        'warning': 25,  # 25% de la capacité CPU (6 cœurs)
        'critical': 20   # 20% pour éviter les pics
    },
    'memory': {
        'warning': 4096,  # 4Go (25% de 16Go)
        'critical': 3072   # 3Go pour éviter les problèmes
    },
    'gpu': {
        'warning': 25,  # 25% de la capacité GPU
        'critical': 20   # 20% pour éviter les surchauffes
    },
    'disk': {
        'warning': 75,  # 75% pour plus de marge
        'critical': 85   # 85% pour éviter les problèmes d'espace
    }
}

# Performance
PERFORMANCE_THRESHOLDS = {
    'response_time': {
        'warning': 500,  # 500ms pour une meilleure performance
        'critical': 1000  # 1s pour éviter les problèmes
    },
    'throughput': {
        'warning': 25,   # 25 req/min pour une utilisation légère
        'critical': 20   # 20 req/min pour éviter les pics
    },
    'error_rate': {
        'warning': 0.5,  # 0.5% pour une meilleure fiabilité
        'critical': 1    # 1% pour éviter les problèmes
    },
    'latency': {
        'warning': 25,   # 25ms pour une meilleure performance
        'critical': 50   # 50ms pour éviter les problèmes
    }
}

# Alertes
ALERT_THRESHOLDS = {
    'failure_rate': {
        'warning': 1,     # 1% pour une meilleure fiabilité
        'critical': 2     # 2% pour éviter les problèmes
    },
    'alert_frequency': {
        'warning': 2,    # 2 alertes/heure pour éviter le spam
        'critical': 4    # 4 alertes/heure pour une meilleure gestion
    },
    'inactive_channels': {
        'warning': 1,     # 1 canal inactif
        'critical': 2     # 2 canaux inactifs
    }
}

# Configuration des fenêtres de temps pour les calculs
TIME_WINDOWS = {
    'short': 60,     # 1 minute
    'medium': 300,   # 5 minutes
    'long': 3600     # 1 heure
}

# Configuration des notifications
NOTIFICATION_CONFIG = {
    'channels': ['email', 'slack'],
    'retry_count': 3,
    'retry_delay': 300,  # 5 minutes
    'batch_size': 100
}
