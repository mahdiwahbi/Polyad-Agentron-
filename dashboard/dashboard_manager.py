import streamlit as st
from config.api.api_manager import load_apis
from config.environments import load_environment
import json

class DashboardManager:
    def __init__(self):
        """Initialise le gestionnaire du dashboard."""
        self.apis = load_apis()
        self.env = load_environment()
        self.logger = st.logger

    def show_dashboard(self):
        """Affiche le dashboard."""
        st.title("Polyad Dashboard")
        
        # Menu de navigation
        pages = {
            "🏠 Accueil": self.show_home,
            "⚙️ Configuration des APIs": self.show_api_config,
            "🌐 Recherche Web": self.show_web_search
        }

        # Sélection de la page
        page = st.sidebar.selectbox(
            "Navigation",
            tuple(pages.keys())
        )

        # Affichage de la page
        pages[page]()

    def show_home(self):
        """Affiche la page d'accueil."""
        st.header("Bienvenue sur le Dashboard Polyad")
        
        # Statistiques
        st.subheader("Statistiques")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("APIs Activées", len([api for api, config in self.apis['apis'].items() if config['enabled']]))
            st.metric("APIs Total", len(self.apis['apis']))
        
        with col2:
            st.metric("Version", self.apis['version'])
            st.metric("APIs de Recherche", len([api for api in self.apis['apis'] if api in ['duckduckgo', 'google_search', 'bing_search', 'serpapi']]))
        
        # Documentation
        st.subheader("Documentation")
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

    def show_api_config(self):
        """Affiche la configuration des APIs."""
        st.header("Configuration des APIs")
        
        for api_name, api_config in self.apis['apis'].items():
            with st.expander(f"{api_name} - {api_config['description']}"):
                # Afficher l'état actuel
                st.write(f"État actuel: {'Activé' if api_config['enabled'] else 'Désactivé'}")
                
                # Champs de configuration
                col1, col2 = st.columns(2)
                
                with col1:
                    # Champs communs
                    enabled = st.checkbox("Activer cette API", value=api_config['enabled'])
                    api_key = st.text_input("Clé API", value=api_config['api_key'])
                    
                with col2:
                    # Informations supplémentaires
                    st.write(f"URL de base: {api_config['base_url']}")
                    st.write(f"Limite de taux: {api_config['rate_limit']} requêtes/minute")
                    st.write(f"Durée de cache: {api_config['cache_ttl']} secondes")
                
                # Bouton pour sauvegarder
                if st.button(f"Sauvegarder {api_name}", key=f"save_{api_name}"):
                    # Mettre à jour la configuration
                    api_config['enabled'] = enabled
                    api_config['api_key'] = api_key
                    
                    # Sauvegarder dans les variables d'environnement si nécessaire
                    if api_key:
                        env_key = f"{api_name.upper()}_API_KEY"
                        os.environ[env_key] = api_key
                    
                    st.success(f"Configuration de {api_name} sauvegardée avec succès!")

    def show_web_search(self):
        """Affiche la recherche web."""
        st.header("Recherche Web")
        
        # Sélectionner l'API de recherche
        search_apis = [api for api, config in self.apis['apis'].items() 
                      if api in ['duckduckgo', 'google_search', 'bing_search', 'serpapi'] and config['enabled']]
        
        if not search_apis:
            st.error("Aucune API de recherche n'est configurée. Veuillez configurer une API de recherche dans la section Configuration des APIs.")
            return
        
        selected_api = st.selectbox("Sélectionner l'API de recherche", search_apis)
        
        # Interface de recherche
        query = st.text_input("Rechercher sur le web")
        
        if query:
            if st.button("Rechercher"):
                with st.spinner("Recherche en cours..."):
                    # Obtenir la configuration de l'API sélectionnée
                    api_config = self.apis['apis'][selected_api]
                    
                    try:
                        # Effectuer la recherche selon l'API sélectionnée
                        if selected_api == 'duckduckgo':
                            params = {
                                'q': query,
                                'format': 'json'
                            }
                            response = requests.get(api_config['base_url'], params=params)
                            results = response.json()
                            
                            # Afficher les résultats
                            st.subheader("Résultats de la recherche")
                            for result in results['Results']:
                                st.write(f"- [{result['Text']}]({result['FirstURL']})")
                        
                        elif selected_api == 'google_search':
                            params = {
                                'key': api_config['api_key'],
                                'cx': os.getenv('GOOGLE_SEARCH_CX'),
                                'q': query
                            }
                            response = requests.get(api_config['base_url'], params=params)
                            results = response.json()
                            
                            # Afficher les résultats
                            st.subheader("Résultats de la recherche")
                            for item in results.get('items', []):
                                st.write(f"- [{item['title']}]({item['link']})")
                        
                        elif selected_api == 'bing_search':
                            headers = {
                                'Ocp-Apim-Subscription-Key': api_config['api_key']
                            }
                            params = {
                                'q': query,
                                'responseFilter': 'WebPages',
                                'count': 5
                            }
                            response = requests.get(api_config['base_url'], headers=headers, params=params)
                            results = response.json()
                            
                            # Afficher les résultats
                            st.subheader("Résultats de la recherche")
                            for web_page in results.get('webPages', {}).get('value', []):
                                st.write(f"- [{web_page['name']}]({web_page['url']})")
                        
                        elif selected_api == 'serpapi':
                            params = {
                                'q': query,
                                'api_key': api_config['api_key']
                            }
                            response = requests.get(api_config['base_url'], params=params)
                            results = response.json()
                            
                            # Afficher les résultats
                            st.subheader("Résultats de la recherche")
                            for result in results.get('organic_results', []):
                                st.write(f"- [{result['title']}]({result['link']})")
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la recherche: {str(e)}")

if __name__ == '__main__':
    dashboard = DashboardManager()
    dashboard.show_dashboard()
