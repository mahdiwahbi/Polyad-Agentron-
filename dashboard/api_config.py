import streamlit as st
from config.api.api_manager import load_apis
from config.environments import load_environment
import json

def api_config_page():
    """Page de configuration des APIs."""
    st.title("Configuration des APIs")
    
    # Charger la configuration
    apis = load_apis()
    env = load_environment()
    
    # Afficher les informations de base
    st.subheader("Informations")
    st.write(f"Version de la configuration: {apis['version']}")
    
    # Créer un formulaire pour chaque API
    for api_name, api_config in apis['apis'].items():
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
    
    # Afficher les logs
    st.subheader("Logs")
    with open('logs/api.log', 'r') as f:
        logs = f.read()
        st.text_area("Logs des APIs", value=logs, height=300)

if __name__ == '__main__':
    api_config_page()
