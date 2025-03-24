from app import server
import webbrowser
import threading
import time
import signal
import sys
import streamlit as st
from pages import home, api_config, web_search

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down dashboard...")
    sys.exit(0)

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:8050/')

def main():
    """Main entry point for the dashboard"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start browser in a separate thread
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start the server
        server.run(debug=True, port=8050, use_reloader=False)
        
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)

def streamlit_main():
    """Application principale du dashboard."""
    st.set_page_config(
        page_title="Polyad Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # Menu de navigation
    pages = {
        "🏠 Accueil": home,
        "⚙️ Configuration des APIs": api_config,
        "🌐 Recherche Web": web_search
    }

    # Sélection de la page
    page = st.sidebar.selectbox(
        "Navigation",
        tuple(pages.keys())
    )

    # Affichage de la page
    pages[page].main()

if __name__ == '__main__':
    main()
    streamlit_main()