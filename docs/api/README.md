# Documentation des APIs Polyad

## Introduction

Polyad intègre désormais de nombreuses APIs externes pour étendre ses fonctionnalités et offrir une expérience utilisateur plus riche. Cette documentation détaille les APIs disponibles, leur utilisation et leur configuration.

## Prérequis

Pour utiliser certaines APIs, vous aurez besoin d'obtenir des clés API auprès des fournisseurs correspondants. Les clés API peuvent être configurées via l'interface graphique de l'application Polyad ou directement dans le fichier de configuration `config/api/apis.json`.

## Architecture

L'intégration des APIs dans Polyad repose sur une architecture modulaire qui utilise les composants existants du système :

```
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│                   │       │                   │       │                   │
│  APIManager       │<─────>│  Cache System     │<─────>│  API Externe      │
│                   │       │                   │       │                   │
└───────────────────┘       └───────────────────┘       └───────────────────┘
         │                           ▲
         │                           │
         ▼                           │
┌───────────────────┐       ┌───────────────────┐
│                   │       │                   │
│  API Spécifiques  │<─────>│  Load Balancer    │
│                   │       │                   │
└───────────────────┘       └───────────────────┘
```

## APIs Intégrées

### 1. Hugging Face

**Description** : Accès à des milliers de modèles de machine learning.

**Fonctionnalités** :
- Génération de texte
- Classification de texte
- Reconnaissance d'entités nommées
- Réponse aux questions
- Résumé de texte
- Traduction

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API Hugging Face
hf_api = get_api_instance(api_manager, "huggingface")

# Générer du texte
response = hf_api.generate_text(
    model_id="gpt2", 
    inputs="Polyad est un assistant IA qui"
)
```

### 2. Wikipedia

**Description** : Recherche d'informations vérifiées.

**Fonctionnalités** :
- Recherche d'articles
- Récupération de résumés
- Information sur les pages
- Récupération d'images

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API Wikipedia
wiki_api = get_api_instance(api_manager, "wikipedia")

# Rechercher des articles
results = wiki_api.search("Intelligence artificielle", limit=5, language="fr")

# Obtenir un résumé
summary = wiki_api.get_summary("Intelligence artificielle", language="fr")
```

### 3. Open-Meteo (Météo)

**Description** : Données météorologiques précises.

**Fonctionnalités** :
- Prévisions météorologiques
- Données historiques
- Données climatiques

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API météo
weather_api = get_api_instance(api_manager, "openmeteo")

# Obtenir les prévisions météo pour Paris
forecast = weather_api.get_forecast(
    latitude=48.8566,
    longitude=2.3522,
    forecast_days=7
)
```

### 4. News API

**Description** : Actualités en temps réel.

**Fonctionnalités** :
- Titres principaux
- Recherche d'articles
- Filtrage par source, pays, catégorie

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API News
news_api = get_api_instance(api_manager, "newsapi")

# Obtenir les titres principaux pour la France
headlines = news_api.get_top_headlines(country="fr", category="technology")

# Rechercher des articles
articles = news_api.search_news("intelligence artificielle", language="fr")
```

### 5. LibreTranslate (Traduction)

**Description** : Support multilingue pour la traduction de texte.

**Fonctionnalités** :
- Traduction de texte
- Détection de langue
- Support de plus de 30 langues

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API de traduction
translation_api = get_api_instance(api_manager, "translation")

# Traduire un texte de l'anglais vers le français
translation = translation_api.translate(
    text="Polyad is an AI assistant that helps you with various tasks.",
    source_lang="en",
    target_lang="fr"
)
```

### 6. OCR.space

**Description** : Reconnaissance optique de caractères dans les images.

**Fonctionnalités** :
- Extraction de texte depuis des images
- Support de nombreuses langues
- Reconnaissance de texte manuscrit

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance
import base64

# Obtenir une instance de l'API OCR
ocr_api = get_api_instance(api_manager, "ocr")

# Charger une image en base64
with open("image.jpg", "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode('utf-8')

# Extraire le texte de l'image
text = ocr_api.extract_text(image_data, language="fra")
```

### 7. Text Analysis

**Description** : Analyse sémantique avancée de texte.

**Fonctionnalités** :
- Analyse de sentiment
- Extraction d'entités
- Détection de la langue
- Extraction de phrases clés

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API d'analyse de texte
text_analysis_api = get_api_instance(api_manager, "textanalysis")

# Analyser le sentiment d'un texte
sentiment = text_analysis_api.sentiment_analysis(
    "J'adore Polyad, c'est un excellent outil !",
    language="fr"
)

# Extraire les entités d'un texte
entities = text_analysis_api.entity_extraction(
    "Paris est la capitale de la France et Emmanuel Macron est son président.",
    language="fr"
)
```

### 8. Meilisearch

**Description** : Moteur de recherche vectorielle pour les données internes.

**Fonctionnalités** :
- Recherche full-text
- Recherche vectorielle
- Typo-tolérance
- Filtres et facettes

**Exemples d'utilisation** :

```python
from core.api_manager import get_api_instance

# Obtenir une instance de l'API Meilisearch
search_api = get_api_instance(api_manager, "meilisearch")

# Rechercher dans un index
results = search_api.search("documents", "intelligence artificielle", limit=20)

# Ajouter des documents à un index
documents = [
    {"id": 1, "title": "Introduction à l'IA", "content": "..."},
    {"id": 2, "title": "Machine Learning", "content": "..."}
]
search_api.add_documents("documents", documents)
```

## Configuration des APIs

Les APIs peuvent être configurées via l'interface graphique de Polyad ou en modifiant directement le fichier de configuration `config/api/apis.json`.

### Structure du fichier de configuration

```json
{
  "version": "2.0.0",
  "apis": {
    "huggingface": {
      "description": "Accès à des milliers de modèles ML",
      "enabled": true,
      "api_key": "",
      "base_url": "https://api-inference.huggingface.co/models/",
      "rate_limit": 100,
      "cache_ttl": 3600
    },
    ...
  },
  "global_settings": {
    "use_cache": true,
    "default_ttl": 3600,
    "load_balancing": true,
    "retry_attempts": 3,
    "timeout": 30
  }
}
```

### Paramètres globaux

- **use_cache** : Activer/désactiver la mise en cache des réponses.
- **default_ttl** : Durée de vie par défaut des éléments en cache (en secondes).
- **load_balancing** : Activer/désactiver l'équilibrage de charge.
- **retry_attempts** : Nombre de tentatives en cas d'échec d'une requête.
- **timeout** : Délai d'expiration des requêtes (en secondes).

### Paramètres API spécifiques

- **description** : Description de l'API.
- **enabled** : Activer/désactiver l'API.
- **api_key** : Clé API pour l'authentification.
- **base_url** : URL de base pour les requêtes API.
- **rate_limit** : Limite de taux de requêtes.
- **cache_ttl** : Durée de vie spécifique pour cette API (en secondes).

## Intégration avec les composants existants de Polyad

### Intégration avec le système de cache

Le gestionnaire d'API utilise le système de cache existant de Polyad pour mettre en cache les réponses des APIs externes. Cela permet de réduire le nombre de requêtes et d'améliorer les performances.

### Intégration avec l'équilibreur de charge

Pour les APIs qui supportent plusieurs points de terminaison, l'équilibreur de charge de Polyad est utilisé pour distribuer les requêtes et améliorer la fiabilité.

### Intégration avec la sécurité

Le gestionnaire d'API respecte les politiques de sécurité de Polyad, notamment en ce qui concerne la gestion des clés API et la protection des données sensibles.

## Conclusion

Les APIs intégrées dans Polyad étendent considérablement ses capacités et permettent de répondre à une large gamme de besoins utilisateurs. La structure modulaire facilite l'ajout de nouvelles APIs à l'avenir.
