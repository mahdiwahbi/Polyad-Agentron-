#!/usr/bin/env python3
import os
import subprocess
import time
from threading import Thread
from flask import Flask
from dash import Dash
from app import app
from components.resource_charts import ResourceCharts

def start_polyad():
    """Démarrer le serveur Polyad"""
    subprocess.Popen(['python', '-m', 'polyad', '--dev', '--config', 'config/config.yaml'])

def start_dashboard():
    """Démarrer le dashboard Dash"""
    try:
        # Attendre que le serveur Polyad démarre
        time.sleep(10)  # Attendre 10 secondes
        
        # Démarrer le dashboard
        app.run(debug=True, port=8050)
    except Exception as e:
        print(f"Error starting dashboard: {e}")

def main():
    # Démarrer le serveur Polyad dans un thread
    polyad_thread = Thread(target=start_polyad)
    polyad_thread.daemon = True
    polyad_thread.start()
    
    # Démarrer le dashboard dans un thread séparé
    dashboard_thread = Thread(target=start_dashboard)
    dashboard_thread.daemon = True
    dashboard_thread.start()
    
    # Attendre que les threads se terminent
    polyad_thread.join()
    dashboard_thread.join()

if __name__ == '__main__':
    main()