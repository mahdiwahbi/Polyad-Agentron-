#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application macOS native pour Polyad
"""
import os
import sys
import json
import time
import signal
import subprocess
import webbrowser
import threading
import socket
import platform
from datetime import datetime

# Path pour les imports relatifs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Vérifier si les modules nécessaires sont disponibles
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QTextEdit, QTabWidget, QProgressBar,
                               QMessageBox, QSystemTrayIcon, QMenu, QSplashScreen, QDialog,
                               QFrame, QGridLayout, QToolButton, QSizePolicy, QSpacerItem,
                               QListWidget, QListWidgetItem, QStyle, QStyleFactory)
    from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont, QColor, QPalette, QCursor, QLinearGradient
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QSize, QPropertyAnimation, QEasingCurve
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    
    # Importer les interfaces des APIs
    from ui.api_config_dialog import show_api_config_dialog
    from ui.api_test_dialog import show_api_test_dialog
except ImportError:
    print("PyQt6 n'est pas installé. Installation en cours...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6", "PyQt6-WebEngine"])
        # Redémarrer le script après l'installation
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"Erreur lors de l'installation de PyQt6: {e}")
        print("Veuillez installer manuellement PyQt6 et PyQt6-WebEngine:")
        print("pip install PyQt6 PyQt6-WebEngine")
        sys.exit(1)

# Définir les chemins
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_COMPOSE_PATH = os.path.join(APP_DIR, "docker-compose.yml")
ENV_FILE_PATH = os.path.join(APP_DIR, ".env.production")

# Ports des services
SERVICE_PORTS = {
    "API": 8000,
    "Dashboard": 8001,
    "Prometheus": 9090,
    "Grafana": 3000
}

class ServiceThread(QThread):
    """Thread qui gère un service en arrière-plan"""
    update_signal = pyqtSignal(str)
    status_signal = pyqtSignal(bool)
    
    def __init__(self, command, cwd=None, env=None):
        super().__init__()
        self.command = command
        self.cwd = cwd or APP_DIR
        self.env = env or os.environ.copy()
        self.process = None
        self.running = False
        
    def run(self):
        self.running = True
        self.update_signal.emit(f"Démarrage du service: {' '.join(self.command)}")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.status_signal.emit(True)
            
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.update_signal.emit(line.rstrip())
            
            if self.process.poll() is not None:
                self.update_signal.emit(f"Le service s'est arrêté avec le code: {self.process.returncode}")
                self.status_signal.emit(False)
                
        except Exception as e:
            self.update_signal.emit(f"Erreur: {str(e)}")
            self.status_signal.emit(False)
            self.running = False
    
    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            try:
                # Tenter un arrêt gracieux d'abord
                if sys.platform == 'win32':
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.process.send_signal(signal.SIGTERM)
                
                # Attendre que le processus se termine
                for _ in range(10):  # Attendre 5 secondes max
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.5)
                
                # S'il ne s'est pas terminé, le forcer
                if self.process.poll() is None:
                    self.process.kill()
                    
            except Exception as e:
                print(f"Erreur lors de l'arrêt du processus: {e}")


class DockerServiceManager:
    """Gestionnaire des services Docker pour Polyad"""
    def __init__(self):
        self.compose_file = DOCKER_COMPOSE_PATH
        self.env_file = ENV_FILE_PATH
        
    def is_docker_running(self):
        """Vérifie si Docker est en cours d'exécution"""
        try:
            result = subprocess.run(["docker", "info"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    def is_ollama_running(self):
        """Vérifie si Ollama est en cours d'exécution"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
            
    def start_services(self):
        """Démarrer les services Docker"""
        cmd = ["docker-compose", "-f", self.compose_file]
        if os.path.exists(self.env_file):
            cmd.extend(["--env-file", self.env_file])
        cmd.extend(["up", "-d"])
        return cmd
    
    def stop_services(self):
        """Arrêter les services Docker"""
        cmd = ["docker-compose", "-f", self.compose_file, "down"]
        return cmd
    
    def check_service_status(self):
        """Vérifier le statut des services Docker"""
        cmd = ["docker-compose", "-f", self.compose_file, "ps"]
        return cmd
        
    def get_service_logs(self, service_name):
        """Obtenir les logs d'un service spécifique"""
        cmd = ["docker-compose", "-f", self.compose_file, "logs", "--tail=100", service_name]
        return cmd


class ServiceStatusWidget(QFrame):
    """Widget qui affiche le statut d'un service"""
    def __init__(self, name, port, parent=None):
        super().__init__(parent)
        self.name = name
        self.port = port
        self.url = f"http://localhost:{port}"
        
        self.initUI()
        
        # Vérifier périodiquement le statut
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_status)
        self.timer.start(5000)  # Vérifier toutes les 5 secondes
        
        # Vérifier immédiatement
        QTimer.singleShot(500, self.check_status)
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # En-tête avec nom et indicateur
        header_layout = QHBoxLayout()
        
        name_label = QLabel(f"{self.name}")
        name_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: white;")
        
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("color: gray; font-size: 16px;")
        self.status_label.setToolTip("Statut de connexion")
        
        header_layout.addWidget(name_label, 1)
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)
        
        # Port info
        info_layout = QHBoxLayout()
        port_label = QLabel(f"Port: {self.port}")
        port_label.setStyleSheet("color: #b0b0b0; font-size: 10pt;")
        info_layout.addWidget(port_label)
        info_layout.addStretch(1)
        layout.addLayout(info_layout)
        
        # Bouton d'ouverture
        self.open_button = QPushButton("Ouvrir dans le navigateur")
        self.open_button.setIcon(QIcon.fromTheme("web-browser"))
        self.open_button.setStyleSheet(
            "QPushButton { background-color: #42a5f5; color: white; border: none; padding: 5px; border-radius: 4px; } " 
            "QPushButton:hover { background-color: #64b5f6; } " 
            "QPushButton:disabled { background-color: #555555; color: #aaaaaa; }"
        )
        self.open_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_button.clicked.connect(self.open_service)
        self.open_button.setEnabled(False)
        layout.addWidget(self.open_button)
        
    def check_status(self):
        """Vérifier si le service répond sur son port"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("localhost", self.port))
            s.close()
            self.set_status(True)
        except (socket.error, socket.timeout):
            self.set_status(False)
        
    def set_status(self, is_running):
        if is_running:
            self.status_label.setStyleSheet("color: #4caf50; font-size: 16px;")
            self.status_label.setToolTip(f"{self.name} est en cours d'exécution")
            self.open_button.setEnabled(True)
            self.setStyleSheet("background-color: #333333; border-radius: 4px; border-left: 3px solid #4caf50;")
        else:
            self.status_label.setStyleSheet("color: #f44336; font-size: 16px;")
            self.status_label.setToolTip(f"{self.name} n'est pas en cours d'exécution")
            self.open_button.setEnabled(False)
            self.setStyleSheet("background-color: #333333; border-radius: 4px; border-left: 3px solid #f44336;")
    
    def open_service(self):
        """Ouvrir le service dans le navigateur"""
        # Animation de clic
        original_style = self.open_button.styleSheet()
        self.open_button.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; border: none; padding: 5px; border-radius: 4px; }"
        )
        QTimer.singleShot(100, lambda: self.open_button.setStyleSheet(original_style))
        
        # Ouvrir le navigateur
        webbrowser.open(self.url)


class PolyadApp(QMainWindow):
    """Application principale Polyad"""
    def __init__(self):
        super().__init__()
        
        self.docker_manager = DockerServiceManager()
        self.service_thread = None
        self.log_thread = None
        
        # Initialiser le gestionnaire d'API
        try:
            from core.api_manager import APIManager
            self.api_manager = APIManager()
        except ImportError:
            self.api_manager = None
            print("Module api_manager non trouvé. Les fonctionnalités API seront désactivées.")
        
        # Configuration de la fenêtre principale
        self.setWindowTitle("Polyad - Plateforme d'intégration d'APIs")
        self.setMinimumSize(1024, 768)
        
        # Application d'un style moderne
        self._setup_style()
        
        # Initialiser l'interface utilisateur
        self.init_ui()
        
        # Vérifier les prérequis
        self.check_prerequisites()
        
        # Créer l'icône de la barre des tâches
        self.setup_tray_icon()
        
    def _setup_style(self):
        """Configure le style moderne de l'application"""
        # Utiliser un style moderne
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        
        # Palette de couleurs modernes
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        # Couleurs pour les éléments désactivés
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
        
        # Appliquer la palette
        QApplication.setPalette(palette)
    
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête avec logo et titre
        header_frame = QFrame()
        header_frame.setObjectName("header")
        header_frame.setStyleSheet("#header { background-color: #2a3990; border-radius: 8px; }")
        header_layout = QHBoxLayout(header_frame)
        
        logo_label = QLabel("Polyad")
        logo_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: white;")
        
        header_layout.addWidget(logo_label)
        header_layout.addStretch(1)
        
        # Boutons d'état dans l'en-tête
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border-radius: 5px; padding: 5px;")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.docker_status = QLabel("Docker: Vérification...")
        self.docker_status.setStyleSheet("color: #f0f0f0;")
        self.ollama_status = QLabel("Ollama: Vérification...")
        self.ollama_status.setStyleSheet("color: #f0f0f0;")
        
        status_layout.addWidget(self.docker_status)
        status_layout.addWidget(self.ollama_status)
        
        header_layout.addWidget(status_frame)
        
        main_layout.addWidget(header_frame)
        
        # Conteneur principal avec barre latérale et contenu
        content_container = QFrame()
        content_container.setStyleSheet("background-color: #2d2d30; border-radius: 8px;")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barre latérale avec navigation et actions
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #252526; border-top-left-radius: 8px; border-bottom-left-radius: 8px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(5)
        sidebar_layout.setContentsMargins(5, 10, 5, 10)
        
        # Titre de la section API
        api_section_label = QLabel("APIs & Intégrations")
        api_section_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        api_section_label.setStyleSheet("color: #42a5f5; padding: 5px; margin-top: 10px;")
        sidebar_layout.addWidget(api_section_label)
        
        # Boutons pour les APIs avec des icônes
        if hasattr(self, "api_manager") and self.api_manager:
            self.api_config_button = QPushButton(" Configurer")
            self.api_config_button.setIcon(QIcon.fromTheme("preferences-system"))
            self.api_config_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.api_config_button.setStyleSheet(
                "QPushButton { text-align: left; background-color: #333333; color: white; border: none; padding: 8px; border-radius: 4px; } " 
                "QPushButton:hover { background-color: #42a5f5; }"
            )
            self.api_config_button.clicked.connect(self.show_api_config)
            sidebar_layout.addWidget(self.api_config_button)
            
            self.api_test_button = QPushButton(" Tester")
            self.api_test_button.setIcon(QIcon.fromTheme("system-run"))
            self.api_test_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.api_test_button.setStyleSheet(
                "QPushButton { text-align: left; background-color: #333333; color: white; border: none; padding: 8px; border-radius: 4px; } " 
                "QPushButton:hover { background-color: #42a5f5; }"
            )
            self.api_test_button.clicked.connect(self.show_api_test)
            sidebar_layout.addWidget(self.api_test_button)
            
            sidebar_layout.addSpacing(10)
        
        # Titre de la section Infrastructure
        infra_section_label = QLabel("Infrastructure")
        infra_section_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        infra_section_label.setStyleSheet("color: #42a5f5; padding: 5px; margin-top: 10px;")
        sidebar_layout.addWidget(infra_section_label)
        
        # Boutons de gestion des services
        self.start_button = QPushButton(" Démarrer Services")
        self.start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_button.setStyleSheet(
            "QPushButton { text-align: left; background-color: #333333; color: white; border: none; padding: 8px; border-radius: 4px; } " 
            "QPushButton:hover { background-color: #4caf50; }"
        )
        self.start_button.clicked.connect(self.start_services)
        sidebar_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton(" Arrêter Services")
        self.stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stop_button.setStyleSheet(
            "QPushButton { text-align: left; background-color: #333333; color: white; border: none; padding: 8px; border-radius: 4px; } " 
            "QPushButton:hover { background-color: #f44336; }"
        )
        self.stop_button.clicked.connect(self.stop_services)
        self.stop_button.setEnabled(False)
        sidebar_layout.addWidget(self.stop_button)
        
        sidebar_layout.addStretch(1)
        content_layout.addWidget(sidebar)
        
        # Contenu principal avec les onglets
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #1e1e1e; border-top-right-radius: 8px; border-bottom-right-radius: 8px;")
        main_content_layout = QVBoxLayout(main_content)
        
        # Tableau des services en format grille
        service_frame = QFrame()
        service_frame.setStyleSheet("background-color: #252526; border-radius: 6px; margin-bottom: 10px;")
        service_layout = QVBoxLayout(service_frame)
        service_title = QLabel("Services Disponibles")
        service_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        service_title.setStyleSheet("color: white; padding-bottom: 5px;")
        service_layout.addWidget(service_title)
        
        services_grid = QGridLayout()
        services_grid.setSpacing(10)
        
        # Ajouter les services dans une grille
        self.service_widgets = {}
        col, row = 0, 0
        for i, (name, port) in enumerate(SERVICE_PORTS.items()):
            service_widget = ServiceStatusWidget(name, port)
            service_widget.setStyleSheet("background-color: #333333; border-radius: 4px; padding: 5px;")
            services_grid.addWidget(service_widget, row, col)
            self.service_widgets[name] = service_widget
            col += 1
            if col > 1:  # 2 colonnes
                col = 0
                row += 1
        
        service_layout.addLayout(services_grid)
        main_content_layout.addWidget(service_frame)
        
        # Onglets pour les journaux et interfaces web
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #333333; background-color: #252526; border-radius: 4px; } " 
            "QTabBar::tab { background-color: #1e1e1e; color: white; padding: 8px 15px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; } " 
            "QTabBar::tab:selected { background-color: #42a5f5; color: white; } " 
            "QTabBar::tab:hover:!selected { background-color: #333333; }"
        )
        
        # Onglet des journaux
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setFont(QFont("Consolas", 10))
        self.log_widget.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0; border: none;")
        self.tabs.addTab(self.log_widget, "Journaux")
        
        # Onglet Dashboard
        self.browser = QWebEngineView()
        self.tabs.addTab(self.browser, "Dashboard")
        
        # Onglet Prometheus
        self.prometheus_browser = QWebEngineView()
        self.tabs.addTab(self.prometheus_browser, "Métriques (Prometheus)")
        
        # Onglet Grafana
        self.grafana_browser = QWebEngineView()
        self.tabs.addTab(self.grafana_browser, "Graphiques (Grafana)")
        
        main_content_layout.addWidget(self.tabs, 1)
        
        # Barre de progression stylisée
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 3px; color: white; height: 20px; text-align: center; } " 
            "QProgressBar::chunk { background-color: #42a5f5; border-radius: 3px; }"
        )
        self.progress_bar.setVisible(False)
        main_content_layout.addWidget(self.progress_bar)
        
        content_layout.addWidget(main_content)
        main_layout.addWidget(content_container, 1)
        
        # Barre de statut modernisée
        self.statusBar().setStyleSheet("background-color: #252526; color: #e0e0e0;")
        self.statusBar().showMessage("Prêt")
    
    def setup_tray_icon(self):
        """Configure l'icône de la barre des tâches"""
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon.fromTheme("applications-system")  # Utiliser une icône système par défaut
        self.tray_icon.setIcon(icon)
        
        # Créer un menu pour l'icône
        tray_menu = QMenu()
        
        # Action pour afficher/masquer la fenêtre
        show_action = QAction("Afficher", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # Séparateur
        tray_menu.addSeparator()
        
        # Action pour démarrer les services
        start_action = QAction("Démarrer les services", self)
        start_action.triggered.connect(self.start_services)
        tray_menu.addAction(start_action)
        
        # Action pour arrêter les services
        stop_action = QAction("Arrêter les services", self)
        stop_action.triggered.connect(self.stop_services)
        tray_menu.addAction(stop_action)
        
        # Séparateur
        tray_menu.addSeparator()
        
        # Action pour quitter
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        
        # Associer le menu à l'icône
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Gérer le clic sur l'icône
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
                self.activateWindow()
    
    def check_prerequisites(self):
        """Vérifier si Docker et Ollama sont installés et en cours d'exécution"""
        # Vérifier Docker
        if self.docker_manager.is_docker_running():
            self.docker_status.setText("Docker: En cours d'exécution")
            self.docker_status.setStyleSheet("color: green;")
            self.start_button.setEnabled(True)
        else:
            self.docker_status.setText("Docker: Arrêté ou non installé")
            self.docker_status.setStyleSheet("color: red;")
            self.start_button.setEnabled(False)
            self.log_message("Docker n'est pas en cours d'exécution. Veuillez démarrer Docker.")
        
        # Vérifier Ollama
        if self.docker_manager.is_ollama_running():
            self.ollama_status.setText("Ollama: En cours d'exécution")
            self.ollama_status.setStyleSheet("color: green;")
        else:
            self.ollama_status.setText("Ollama: Arrêté ou non installé")
            self.ollama_status.setStyleSheet("color: red;")
            self.log_message("Ollama n'est pas en cours d'exécution. Veuillez démarrer Ollama.")
            
        # Planifier une vérification périodique
        timer = QTimer(self)
        timer.timeout.connect(self.update_status)
        timer.start(5000)  # Vérifier toutes les 5 secondes
    
    def update_status(self):
        """Mettre à jour le statut des services"""
        # Vérifier Docker et Ollama
        self.check_prerequisites()
        
        # Vérifier si des services sont en cours d'exécution
        services_running = any(widget.open_button.isEnabled() for widget in self.service_widgets.values())
        self.stop_button.setEnabled(services_running)
    
    def start_services(self):
        """Démarrer tous les services Polyad"""
        if not self.docker_manager.is_docker_running():
            QMessageBox.warning(self, "Erreur", "Docker n'est pas en cours d'exécution. Veuillez démarrer Docker.")
            return
            
        if not self.docker_manager.is_ollama_running():
            reply = QMessageBox.question(self, "Attention", 
                                      "Ollama ne semble pas être en cours d'exécution. Continuer quand même?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                      QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Démarrer les services Docker
        self.log_message("Démarrage des services Polyad...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indicateur indéterminé
        
        # Désactiver le bouton
        self.start_button.setEnabled(False)
        
        # Démarrer le thread de service
        if self.service_thread and self.service_thread.isRunning():
            self.service_thread.stop()
            
        self.service_thread = ServiceThread(self.docker_manager.start_services())
        self.service_thread.update_signal.connect(self.log_message)
        self.service_thread.status_signal.connect(self.service_started)
        self.service_thread.start()
    
    def service_started(self, success):
        """Callback lorsque les services sont démarrés"""
        self.progress_bar.setVisible(False)
        self.start_button.setEnabled(True)
        
        if success:
            self.log_message("Services Polyad démarrés avec succès!")
            self.statusBar().showMessage("Services en cours d'exécution")
            self.stop_button.setEnabled(True)
            
            # Démarrer le thread de logs
            if self.log_thread and self.log_thread.isRunning():
                self.log_thread.stop()
                
            self.log_thread = ServiceThread(self.docker_manager.check_service_status())
            self.log_thread.update_signal.connect(self.log_message)
            self.log_thread.start()
            
            # Attendre que les services soient prêts
            QTimer.singleShot(3000, self.load_dashboards)
        else:
            self.log_message("Échec du démarrage des services Polyad")
            self.statusBar().showMessage("Erreur lors du démarrage des services")
    
    def load_dashboards(self):
        """Charger les dashboards dans les onglets du navigateur"""
        # Charger le dashboard principal
        self.browser.load(QUrl(f"http://localhost:{SERVICE_PORTS['Dashboard']}"))
        self.tabs.setCurrentIndex(1)  # Afficher l'onglet Dashboard
        
        # Charger Prometheus
        self.prometheus_browser.load(QUrl(f"http://localhost:{SERVICE_PORTS['Prometheus']}"))
        
        # Charger Grafana
        self.grafana_browser.load(QUrl(f"http://localhost:{SERVICE_PORTS['Grafana']}"))
    
    def stop_services(self):
        """Arrêter tous les services Polyad"""
        reply = QMessageBox.question(self, "Confirmation", 
                                  "Voulez-vous vraiment arrêter tous les services Polyad?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                  QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        self.log_message("Arrêt des services Polyad...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indicateur indéterminé
        
        # Désactiver le bouton
        self.stop_button.setEnabled(False)
        
        # Arrêter les threads existants
        if self.service_thread and self.service_thread.isRunning():
            self.service_thread.stop()
            
        if self.log_thread and self.log_thread.isRunning():
            self.log_thread.stop()
            
        # Démarrer le thread d'arrêt
        self.service_thread = ServiceThread(self.docker_manager.stop_services())
        self.service_thread.update_signal.connect(self.log_message)
        self.service_thread.status_signal.connect(self.service_stopped)
        self.service_thread.start()
    
    def service_stopped(self, success):
        """Callback lorsque les services sont arrêtés"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message("Services Polyad arrêtés avec succès!")
            self.statusBar().showMessage("Services arrêtés")
        else:
            self.log_message("Problème lors de l'arrêt des services Polyad")
            self.statusBar().showMessage("Erreur lors de l'arrêt des services")
            
        # Réactiver le bouton de démarrage
        self.start_button.setEnabled(True)
    
    def log_message(self, message):
        """Ajouter un message aux journaux"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        """Gestion de l'événement de fermeture de l'application"""
        # Vérifier si les services sont en cours d'exécution
        services_running = any(widget.open_button.isEnabled() for widget in self.service_widgets.values())
        
        if services_running:
            reply = QMessageBox.question(
                self, "Confirmation", 
                "Des services sont en cours d'exécution. Voulez-vous les arrêter avant de quitter?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # Arrêter les services
                cmd = self.docker_manager.stop_services()
                try:
                    subprocess.run(cmd, check=True)
                    self.log_message("Services arrêtés")
                except subprocess.CalledProcessError as e:
                    self.log_message(f"Erreur lors de l'arrêt des services: {e}")
        
        # Arrêter les threads
        if self.service_thread and self.service_thread.isRunning():
            self.service_thread.stop()
            
        if self.log_thread and self.log_thread.isRunning():
            self.log_thread.stop()
        
        # Masquer dans la barre des tâches au lieu de fermer
        if QSystemTrayIcon.isSystemTrayAvailable() and not event.spontaneous():
            self.hide()
            self.tray_icon.showMessage(
                "Polyad", 
                "Polyad continue à fonctionner en arrière-plan. Cliquez sur l'icône pour afficher à nouveau.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            # Fermer complètement
            self.close_application()
    
    def show_api_config(self):
        """Afficher le dialogue de configuration des APIs"""
        if hasattr(self, "api_manager") and self.api_manager:
            if show_api_config_dialog(self.api_manager, self):
                self.log_message("Configuration des APIs mise à jour")
                # Recharger l'API manager
                self.api_manager._load_config()
                self.api_manager._initialize_apis()
        else:
            QMessageBox.warning(self, "Erreur", "Gestionnaire d'API non initialisé")
    
    def show_api_test(self):
        """Afficher le dialogue de test des APIs"""
        if hasattr(self, "api_manager") and self.api_manager:
            self.log_message("Lancement de l'utilitaire de test des APIs")
            show_api_test_dialog(self.api_manager, self)
        else:
            QMessageBox.warning(self, "Erreur", "Gestionnaire d'API non initialisé")
            
    def close_application(self):
        """Fermer complètement l'application"""
        # Arrêter tous les threads
        if self.service_thread and self.service_thread.isRunning():
            self.service_thread.stop()
            
        if self.log_thread and self.log_thread.isRunning():
            self.log_thread.stop()
        
        # Arrêter les services si nécessaire
        services_running = any(widget.open_button.isEnabled() for widget in self.service_widgets.values())
        if services_running:
            cmd = self.docker_manager.stop_services()
            try:
                subprocess.run(cmd, check=True)
            except Exception:
                pass
        
        # Supprimer l'icône de la barre des tâches
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quitter l'application
        QApplication.quit()


def main():
    # Créer l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Polyad")
    
    # Créer et afficher la fenêtre principale
    window = PolyadApp()
    window.show()
    
    # Exécuter l'application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
