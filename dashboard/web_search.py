import streamlit as st
from config.api.api_manager import load_apis
import requests
import json

def web_search_page():
    """Page de recherche web."""
    st.title("Recherche Web")
    
    # Charger la configuration des APIs
    apis = load_apis()
    
    # Sélectionner l'API de recherche
    search_apis = [api for api, config in apis['apis'].items() 
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
                api_config = apis['apis'][selected_api]
                
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
    web_search_page()
