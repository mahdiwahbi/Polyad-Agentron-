SYSTEM_CONFIG = {
    # Configuration système
    'system': {
        'cpu_cores': 6,
        'memory_total': 16 * (1024 ** 3),  # 16Go RAM
        'gpu_vram': 4 * (1024 ** 3),      # 4Go VRAM
        'disk_total': 512 * (1024 ** 3),   # 512Go disque
        'max_temperature': 80,             # 80°C maximum
        'min_free_memory': 4 * (1024 ** 3) # 4Go minimum libre
    },

    # Limites de sécurité
    'safety_limits': {
        'cpu': {
            'max_usage': 25,               # 25% maximum
            'warning_threshold': 20,       # 20% warning
            'critical_threshold': 15       # 15% critical
        },
        'memory': {
            'min_available': 4 * (1024 ** 3),  # 4Go minimum
            'warning_threshold': 3 * (1024 ** 3),  # 3Go warning
            'critical_threshold': 2 * (1024 ** 3)  # 2Go critical
        },
        'gpu': {
            'max_usage': 25,               # 25% maximum
            'warning_threshold': 20,       # 20% warning
            'critical_threshold': 15       # 15% critical
        },
        'disk': {
            'max_usage': 75,               # 75% maximum
            'warning_threshold': 70,       # 70% warning
            'critical_threshold': 85       # 85% critical
        },
        'temperature': {
            'max': 80,                    # 80°C maximum
            'warning_threshold': 75,      # 75°C warning
            'critical_threshold': 85      # 85°C critical
        }
    },

    # Intervals de surveillance
    'monitoring_intervals': {
        'cpu': 5,                         # 5 secondes
        'memory': 10,                     # 10 secondes
        'gpu': 10,                        # 10 secondes
        'disk': 30,                       # 30 secondes
        'temperature': 30                 # 30 secondes
    },

    # Configuration des notifications
    'notifications': {
        'channels': ['email', 'slack'],
        'alert_frequency': {
            'warning': 2,                  # 2/h maximum
            'critical': 4                 # 4/h maximum
        },
        'retry_attempts': 3,
        'retry_delay': 60                 # 60 secondes entre tentatives
    }
}
