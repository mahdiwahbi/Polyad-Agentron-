import streamlit as st
from config.api.api_manager import load_apis

def main():
    """Page d'accueil du dashboard."""
    st.title("Bienvenue sur le Dashboard Polyad")
    
    # Statistiques
    st.header("Statistiques")
    
    # Charger la configuration des APIs
    apis = load_apis()
    
    # Afficher les statistiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("APIs Activées", len([api for api, config in apis['apis'].items() if config['enabled']]))
        st.metric("APIs Total", len(apis['apis']))
    
    with col2:
        st.metric("Version", apis['version'])
        st.metric("APIs de Recherche", len([api for api in apis['apis'] if api in ['duckduckgo', 'google_search', 'bing_search', 'serpapi']]))
    
    # Documentation
    st.header("Documentation")
    st.markdown("""
    ## Configuration des APIs
    
    La section "Configuration des APIs" vous permet de :
    - Activer/désactiver les APIs
    - Configurer les clés API
    - Voir les limites de taux et la durée de cache
    
    ## Recherche Web
    
    La section "Recherche Web" vous permet de :
    - Effectuer des recherches sur le web
    - Choisir entre différentes APIs de recherche (DuckDuckGo, Google, Bing, SerpAPI)
    - Voir les résultats formatés
    """)
