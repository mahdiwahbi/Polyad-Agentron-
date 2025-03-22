import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load_environment()
        self.load_yaml()
        self.override_with_env()

    def load_environment(self) -> None:
        """Charger les variables d'environnement"""
        load_dotenv()

    def load_yaml(self) -> None:
        """Charger la configuration depuis le fichier YAML"""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                self.config.update(yaml.safe_load(f))

    def override_with_env(self) -> None:
        """Remplacer les valeurs de configuration par les variables d'environnement"""
        for key, value in self.config.items():
            env_value = os.getenv(key.upper())
            if env_value is not None:
                try:
                    # Convertir la valeur en type approprié
                    if isinstance(value, bool):
                        self.config[key] = env_value.lower() in ["true", "1", "yes", "on"]
                    elif isinstance(value, int):
                        self.config[key] = int(env_value)
                    elif isinstance(value, float):
                        self.config[key] = float(env_value)
                    else:
                        self.config[key] = env_value
                except ValueError:
                    pass

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Obtenir une valeur de configuration"""
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Accès direct à une valeur de configuration"""
        return self.config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Modifier une valeur de configuration"""
        self.config[key] = value

    def __contains__(self, key: str) -> bool:
        """Vérifier si une clé existe dans la configuration"""
        return key in self.config

    def as_dict(self) -> Dict[str, Any]:
        """Obtenir la configuration complète comme dictionnaire"""
        return self.config.copy()

    def save(self) -> None:
        """Sauvegarder la configuration dans un fichier YAML"""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

def load_config() -> ConfigManager:
    """Charger la configuration globale"""
    return ConfigManager()
