#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'APIs pour Polyad
Gère les connexions aux différentes APIs externes intégrées
"""
import os
import json
import time
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin

class APIManager:
    """
    Gestionnaire centralisé pour toutes les APIs externes intégrées à Polyad.
    Supporte:
    - Mise en cache des réponses
    - Gestion des limites de taux
    - Gestion des clés API
    - Équilibrage de charge pour les APIs ayant plusieurs endpoints
    """

    def __init__(self, config_path: str = None, cache_manager=None, load_balancer=None):
        """
        Initialise le gestionnaire d'APIs
        
        Args:
            config_path: Chemin vers la configuration des APIs
            cache_manager: Gestionnaire de cache optionnel (utilise MemoryCache par défaut)
            load_balancer: Équilibreur de charge optionnel pour les APIs avec plusieurs endpoints
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or os.path.join("config", "api", "apis.json")
        self._load_config()
        
        # Intégration avec les composants existants de Polyad
        self.cache_manager = cache_manager
        self.load_balancer = load_balancer
        
        # État interne
        self.rate_limits = {}
        self.active_apis = {}
        self.session = requests.Session()
        
        # Vérifier quelles APIs sont disponibles
        self._initialize_apis()
    
    def _load_config(self):
        """Charge la configuration des APIs depuis le fichier de configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration des APIs chargée depuis {self.config_path}")
            else:
                self.logger.warning(f"Fichier de configuration {self.config_path} non trouvé, utilisation des valeurs par défaut")
                self.config = {
                    "version": "2.0.0",
                    "apis": {},
                    "global_settings": {
                        "use_cache": True,
                        "default_ttl": 3600,
                        "load_balancing": True,
                        "retry_attempts": 3,
                        "timeout": 30
                    }
                }
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration des APIs: {e}")
            self.config = {"apis": {}, "global_settings": {"use_cache": True, "default_ttl": 3600}}
    
    def _initialize_apis(self):
        """Vérifie quelles APIs sont disponibles et les initialise"""
        for api_name, api_config in self.config.get("apis", {}).items():
            if api_config.get("enabled", True):
                try:
                    # Tester la connexion à l'API (peut être personnalisé par API)
                    if self._test_api_connection(api_name, api_config):
                        self.active_apis[api_name] = api_config
                        self.logger.info(f"API {api_name} initialisée avec succès")
                    else:
                        self.logger.warning(f"API {api_name} n'a pas pu être initialisée")
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'initialisation de l'API {api_name}: {e}")
        
        self.logger.info(f"Initialisation complète. APIs actives: {list(self.active_apis.keys())}")
    
    def _test_api_connection(self, api_name: str, api_config: Dict) -> bool:
        """
        Teste la connexion à une API spécifique
        
        Args:
            api_name: Nom de l'API
            api_config: Configuration de l'API
            
        Returns:
            bool: True si l'API est disponible, False sinon
        """
        # Ce test pourrait être remplacé par une vérification spécifique à chaque API
        # Pour l'instant, on considère que l'API est disponible si elle a une configuration
        return True
    
    def get_active_apis(self) -> List[str]:
        """
        Retourne la liste des APIs actives
        
        Returns:
            List[str]: Liste des noms des APIs actives
        """
        return list(self.active_apis.keys())
    
    def get_api_info(self, api_name: str) -> Dict:
        """
        Retourne les informations sur une API
        
        Args:
            api_name: Nom de l'API
            
        Returns:
            Dict: Informations sur l'API
        """
        return self.active_apis.get(api_name, {})
    
    def call_api(self, api_name: str, endpoint: str, method: str = "GET", 
                params: Dict = None, data: Dict = None, headers: Dict = None,
                use_cache: bool = None, cache_ttl: int = None) -> Dict:
        """
        Appelle une API externe
        
        Args:
            api_name: Nom de l'API à appeler
            endpoint: Point de terminaison de l'API
            method: Méthode HTTP (GET, POST, etc.)
            params: Paramètres de requête
            data: Données pour les requêtes POST/PUT
            headers: En-têtes HTTP supplémentaires
            use_cache: Utiliser le cache (si None, utilise la configuration globale)
            cache_ttl: Durée de vie du cache en secondes (si None, utilise la configuration globale)
            
        Returns:
            Dict: Réponse de l'API
        
        Raises:
            ValueError: Si l'API n'existe pas ou n'est pas active
            Exception: Si une erreur se produit lors de l'appel à l'API
        """
        if api_name not in self.active_apis:
            raise ValueError(f"API {api_name} non disponible ou non configurée")
        
        api_config = self.active_apis[api_name]
        global_settings = self.config.get("global_settings", {})
        
        # Déterminer si nous devons utiliser le cache
        should_use_cache = use_cache if use_cache is not None else api_config.get("use_cache", global_settings.get("use_cache", True))
        cache_key = f"{api_name}:{endpoint}:{method}:{str(params)}:{str(data)}"
        
        # Vérifier le cache si activé et si nous avons un gestionnaire de cache
        if should_use_cache and self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                self.logger.debug(f"Résultat trouvé dans le cache pour {cache_key}")
                return cached_result
        
        # Préparer les en-têtes
        request_headers = {"User-Agent": "Polyad/2.0.0"}
        if headers:
            request_headers.update(headers)
            
        # Ajouter la clé API si nécessaire
        api_key = api_config.get("api_key")
        if api_key:
            if api_name == "huggingface":
                request_headers["Authorization"] = f"Bearer {api_key}"
            elif api_name in ["newsapi", "openmeteo", "textanalysis"]:
                params = params or {}
                params["apiKey"] = api_key
            else:
                # Par défaut, ajouter comme paramètre
                params = params or {}
                params["api_key"] = api_key
        
        # Construire l'URL
        base_url = api_config.get("base_url", "")
        url = urljoin(base_url, endpoint) if base_url else endpoint
        
        # Respecter les limites de taux
        self._respect_rate_limits(api_name, api_config)
        
        # Effectuer la requête
        retry_attempts = api_config.get("retry_attempts", global_settings.get("retry_attempts", 3))
        timeout = api_config.get("timeout", global_settings.get("timeout", 30))
        
        for attempt in range(retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if method.upper() in ["POST", "PUT", "PATCH"] else None,
                    headers=request_headers,
                    timeout=timeout
                )
                
                # Mettre à jour le suivi des limites de taux
                self._update_rate_limits(api_name, response.headers)
                
                # Vérifier si la réponse est réussie
                response.raise_for_status()
                
                # Analyser la réponse
                result = response.json() if response.content else {}
                
                # Mettre en cache le résultat si nécessaire
                if should_use_cache and self.cache_manager:
                    ttl = cache_ttl or api_config.get("cache_ttl", global_settings.get("default_ttl", 3600))
                    self.cache_manager.set(cache_key, result, ttl)
                
                return result
                
            except requests.RequestException as e:
                last_error = str(e)
                self.logger.warning(f"Tentative {attempt+1}/{retry_attempts} échouée pour {url}: {last_error}")
                if attempt == retry_attempts - 1:
                    raise Exception(f"Erreur lors de l'appel à {url}: {last_error}")
                time.sleep(2 ** attempt)  # Backoff exponentiel
        
        raise Exception(f"Toutes les tentatives ont échoué pour {url}")
    
    def _respect_rate_limits(self, api_name: str, api_config: Dict):
        """
        Respecte les limites de taux pour une API
        
        Args:
            api_name: Nom de l'API
            api_config: Configuration de l'API
        """
        rate_limit = self.rate_limits.get(api_name, {})
        if "reset_at" in rate_limit and "remaining" in rate_limit:
            # S'il ne reste plus de requêtes autorisées
            if rate_limit["remaining"] <= 0:
                # Calculer le temps à attendre
                now = time.time()
                wait_time = max(0, rate_limit["reset_at"] - now)
                if wait_time > 0:
                    self.logger.info(f"Limite de taux atteinte pour {api_name}. Attente de {wait_time:.2f} secondes.")
                    time.sleep(wait_time)
    
    def _update_rate_limits(self, api_name: str, headers: Dict):
        """
        Met à jour les informations de limite de taux en fonction des en-têtes de réponse
        
        Args:
            api_name: Nom de l'API
            headers: En-têtes de la réponse HTTP
        """
        # Différentes APIs ont différents formats d'en-têtes pour les limites de taux
        # Ceci est une implémentation générique qui devrait être adaptée pour chaque API
        rate_limit_remaining = headers.get("X-RateLimit-Remaining")
        rate_limit_reset = headers.get("X-RateLimit-Reset")
        
        if rate_limit_remaining and rate_limit_reset:
            try:
                self.rate_limits[api_name] = {
                    "remaining": int(rate_limit_remaining),
                    "reset_at": int(rate_limit_reset)
                }
            except (ValueError, TypeError):
                pass
    
    def update_api_key(self, api_name: str, api_key: str) -> bool:
        """
        Met à jour la clé API pour une API spécifique
        
        Args:
            api_name: Nom de l'API
            api_key: Nouvelle clé API
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        if api_name not in self.config.get("apis", {}):
            return False
        
        try:
            # Mettre à jour la configuration
            self.config["apis"][api_name]["api_key"] = api_key
            
            # Mettre à jour le fichier de configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Mettre à jour l'API active si elle existe
            if api_name in self.active_apis:
                self.active_apis[api_name]["api_key"] = api_key
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour de la clé API pour {api_name}: {e}")
            return False
    
    def enable_api(self, api_name: str, enabled: bool = True) -> bool:
        """
        Active ou désactive une API
        
        Args:
            api_name: Nom de l'API
            enabled: True pour activer, False pour désactiver
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        if api_name not in self.config.get("apis", {}):
            return False
        
        try:
            # Mettre à jour la configuration
            self.config["apis"][api_name]["enabled"] = enabled
            
            # Mettre à jour le fichier de configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Mettre à jour les APIs actives
            if enabled:
                if api_name not in self.active_apis and self._test_api_connection(api_name, self.config["apis"][api_name]):
                    self.active_apis[api_name] = self.config["apis"][api_name]
            else:
                if api_name in self.active_apis:
                    del self.active_apis[api_name]
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation/désactivation de l'API {api_name}: {e}")
            return False


# Implémentations d'API spécifiques

class HuggingFaceAPI:
    """Interface pour l'API Hugging Face"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "huggingface"
    
    def get_models(self, filter_criteria=None):
        """Récupère la liste des modèles disponibles sur Hugging Face"""
        params = {}
        if filter_criteria:
            params.update(filter_criteria)
        return self.api_manager.call_api(
            self.api_name, 
            "models", 
            params=params
        )
    
    def generate_text(self, model_id, inputs, parameters=None):
        """Génère du texte avec un modèle spécifique"""
        data = {"inputs": inputs}
        if parameters:
            data["parameters"] = parameters
        return self.api_manager.call_api(
            self.api_name,
            f"models/{model_id}",
            method="POST",
            data=data
        )


class WikipediaAPI:
    """Interface pour l'API Wikipedia"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "wikipedia"
    
    def search(self, query, limit=5, language="fr"):
        """Recherche des articles Wikipedia"""
        return self.api_manager.call_api(
            self.api_name,
            "search",
            params={"q": query, "limit": limit, "language": language}
        )
    
    def get_summary(self, title, language="fr"):
        """Récupère le résumé d'un article Wikipedia"""
        return self.api_manager.call_api(
            self.api_name,
            "summary",
            params={"title": title, "language": language}
        )


class WeatherAPI:
    """Interface pour l'API météo Open-Meteo"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "openmeteo"
    
    def get_forecast(self, latitude, longitude, forecast_days=7):
        """Récupère les prévisions météo pour un emplacement donné"""
        return self.api_manager.call_api(
            self.api_name,
            "forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": forecast_days,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto"
            }
        )


class NewsAPI:
    """Interface pour l'API News"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "newsapi"
    
    def get_top_headlines(self, country="fr", category=None, q=None, page_size=10):
        """Récupère les titres principaux"""
        params = {"country": country, "pageSize": page_size}
        if category:
            params["category"] = category
        if q:
            params["q"] = q
        return self.api_manager.call_api(
            self.api_name,
            "top-headlines",
            params=params
        )
    
    def search_news(self, q, language="fr", sort_by="publishedAt", page_size=10):
        """Recherche des articles"""
        return self.api_manager.call_api(
            self.api_name,
            "everything",
            params={
                "q": q,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size
            }
        )


class TranslationAPI:
    """Interface pour l'API de traduction"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "translation"
    
    def translate(self, text, source_lang="auto", target_lang="fr"):
        """Traduit un texte"""
        return self.api_manager.call_api(
            self.api_name,
            "translate",
            method="POST",
            data={
                "text": text,
                "source": source_lang,
                "target": target_lang
            }
        )


class OCRAPI:
    """Interface pour l'API de reconnaissance optique de caractères"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "ocr"
    
    def extract_text(self, image_data, language="fra"):
        """Extrait le texte d'une image"""
        return self.api_manager.call_api(
            self.api_name,
            "parse",
            method="POST",
            data={"image": image_data, "language": language}
        )


class TextAnalysisAPI:
    """Interface pour l'API d'analyse de texte"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "textanalysis"
    
    def sentiment_analysis(self, text, language="fr"):
        """Analyse le sentiment d'un texte"""
        return self.api_manager.call_api(
            self.api_name,
            "sentiment",
            method="POST",
            data={"text": text, "language": language}
        )
    
    def entity_extraction(self, text, language="fr"):
        """Extrait les entités d'un texte"""
        return self.api_manager.call_api(
            self.api_name,
            "entities",
            method="POST",
            data={"text": text, "language": language}
        )


class MeilisearchAPI:
    """Interface pour l'API Meilisearch"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.api_name = "meilisearch"
    
    def search(self, index, query, limit=20):
        """Recherche dans un index"""
        return self.api_manager.call_api(
            self.api_name,
            f"indexes/{index}/search",
            method="POST",
            data={"q": query, "limit": limit}
        )
    
    def add_documents(self, index, documents):
        """Ajoute des documents à un index"""
        return self.api_manager.call_api(
            self.api_name,
            f"indexes/{index}/documents",
            method="POST",
            data=documents
        )


def get_api_instance(api_manager, api_name):
    """
    Fonction utilitaire pour obtenir une instance d'API spécifique
    
    Args:
        api_manager: Instance d'APIManager
        api_name: Nom de l'API
        
    Returns:
        Instance de l'API demandée
    """
    api_classes = {
        "huggingface": HuggingFaceAPI,
        "wikipedia": WikipediaAPI,
        "openmeteo": WeatherAPI,
        "newsapi": NewsAPI,
        "translation": TranslationAPI,
        "ocr": OCRAPI,
        "textanalysis": TextAnalysisAPI,
        "meilisearch": MeilisearchAPI
    }
    
    if api_name in api_classes:
        return api_classes[api_name](api_manager)
    else:
        raise ValueError(f"API {api_name} non prise en charge")
