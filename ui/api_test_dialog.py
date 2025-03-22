#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface de test des APIs pour Polyad
Permet de tester les APIs externes intégrées
"""
import os
import json
import time
import logging
import traceback
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, 
    QFormLayout, QMessageBox, QProgressBar, QGroupBox,
    QScrollArea
)
from PyQt6.QtGui import QIcon, QFont, QCursor, QTextCursor, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtCore import QRegularExpression

class ApiTestWorker(QThread):
    """Thread pour tester une API en arrière-plan"""
    finished = pyqtSignal(bool, str, object)
    progress = pyqtSignal(int, str)
    
    def __init__(self, api_manager, api_name, method_name, params):
        """
        Initialise le thread de test
        
        Args:
            api_manager: Gestionnaire d'API
            api_name: Nom de l'API à tester
            method_name: Méthode à appeler
            params: Paramètres de la méthode
        """
        super().__init__()
        self.api_manager = api_manager
        self.api_name = api_name
        self.method_name = method_name
        self.params = params
        
    def run(self):
        """Exécute le test en arrière-plan"""
        try:
            self.progress.emit(10, f"Initialisation de l'API {self.api_name}...")
            
            # Obtenir l'API
            api = self.api_manager.get_api(self.api_name)
            if not api:
                self.finished.emit(False, f"API {self.api_name} non disponible", None)
                return
                
            self.progress.emit(30, f"API {self.api_name} initialisée, appel de {self.method_name}...")
            
            # Appel de la méthode
            method = getattr(api, self.method_name, None)
            if not method:
                self.finished.emit(False, f"Méthode {self.method_name} non disponible", None)
                return
                
            # Exécuter la méthode
            self.progress.emit(50, f"Exécution de {self.method_name}...")
            result = method(**self.params)
            
            self.progress.emit(90, "Traitement des résultats...")
            
            # Vérifier les résultats
            success = result is not None
            message = "Succès" if success else "Échec"
            
            self.progress.emit(100, "Terminé")
            self.finished.emit(success, message, result)
            
        except Exception as e:
            self.progress.emit(100, f"Erreur: {str(e)}")
            error_details = traceback.format_exc()
            self.finished.emit(False, f"Erreur: {str(e)}", error_details)


class APITestDialog(QDialog):
    """
    Dialogue de test des APIs pour Polyad
    Permet à l'utilisateur de:
    - Sélectionner une API à tester
    - Configurer les paramètres du test
    - Exécuter le test
    - Visualiser les résultats
    """
    
    def __init__(self, api_manager=None, parent=None):
        """
        Initialise le dialogue de test
        
        Args:
            api_manager: Gestionnaire d'API
            parent: Widget parent
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.api_manager = api_manager
        self.test_worker = None
        
        self.setWindowTitle("Test des APIs")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(QIcon.fromTheme("applications-science"))
        
        # Application d'un style moderne
        self._setup_style()
        
        self._init_ui()
    
    def _setup_style(self):
        """Configure le style moderne du dialogue"""
        # Style global du dialogue
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #f0f0f0; }
            QTabWidget::pane { border: 1px solid #333333; background-color: #252526; border-radius: 4px; } 
            QTabBar::tab { background-color: #1e1e1e; color: white; padding: 8px 15px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; } 
            QTabBar::tab:selected { background-color: #42a5f5; color: white; } 
            QTabBar::tab:hover:!selected { background-color: #333333; }
            QLabel { color: #e0e0e0; }
            QPushButton { background-color: #333333; color: white; border: none; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #42a5f5; }
            QPushButton:disabled { background-color: #555555; color: #aaaaaa; }
            QLineEdit, QSpinBox, QTextEdit { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 4px; }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 1px solid #42a5f5; }
            QCheckBox { color: #e0e0e0; }
            QCheckBox::indicator { width: 15px; height: 15px; }
            QCheckBox::indicator:unchecked { background-color: #333333; border: 1px solid #555555; border-radius: 3px; }
            QCheckBox::indicator:checked { background-color: #42a5f5; border: 1px solid #42a5f5; border-radius: 3px; }
            QComboBox { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 4px; }
            QComboBox:focus { border: 1px solid #42a5f5; }
            QComboBox QAbstractItemView { background-color: #252526; color: white; selection-background-color: #42a5f5; }
            QProgressBar { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #42a5f5; border-radius: 4px; }
            QTableWidget { background-color: #252526; alternate-background-color: #2d2d30; color: white; gridline-color: #444444; }
            QTableWidget::item:selected { background-color: #42a5f5; }
            QHeaderView::section { background-color: #333333; color: white; padding: 5px; border: none; }
            QScrollArea { background-color: #1e1e1e; border: none; }
            QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }
        """)
    
    def _init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # En-tête avec titre et description
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #2a3990; border-radius: 8px; padding: 10px;")
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Test des intégrations API")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        desc_label = QLabel("Vérifiez le fonctionnement des APIs intégrées et testez les réponses en temps réel.")
        desc_label.setStyleSheet("color: #e0e0e0;")
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header_frame)
        
        # Sélection de l'API avec style moderne
        selection_group = QGroupBox("Sélection de l'API")
        selection_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        selection_layout = QFormLayout()
        selection_layout.setContentsMargins(15, 15, 15, 15)
        selection_layout.setSpacing(10)
        
        # Combobox améliorés pour la sélection d'API
        self.api_combo = QComboBox()
        self.api_combo.setStyleSheet(
            "QComboBox { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 6px; }"
            "QComboBox:focus { border: 1px solid #42a5f5; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox::down-arrow { image: url(:/icons/down_arrow.png); width: 12px; height: 12px; }"
        )
        self._populate_api_combo()
        self.api_combo.currentIndexChanged.connect(self._on_api_changed)
        
        self.method_combo = QComboBox()
        self.method_combo.setStyleSheet(
            "QComboBox { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 6px; }"
            "QComboBox:focus { border: 1px solid #42a5f5; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            "QComboBox::down-arrow { image: url(:/icons/down_arrow.png); width: 12px; height: 12px; }"
        )
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        
        selection_layout.addRow("API:", self.api_combo)
        selection_layout.addRow("Méthode:", self.method_combo)
        
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # Paramètres avec style moderne
        self.params_group = QGroupBox("Paramètres de la requête")
        self.params_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        self.params_layout = QFormLayout(self.params_group)
        self.params_layout.setContentsMargins(15, 15, 15, 15)
        self.params_layout.setSpacing(10)
        
        # Zone de défilement améliorée pour les paramètres
        params_scroll = QScrollArea()
        params_scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
            "QScrollBar:vertical { background-color: #252526; width: 12px; margin: 0px; }"
            "QScrollBar::handle:vertical { background-color: #555555; min-height: 20px; border-radius: 6px; }"
            "QScrollBar::handle:vertical:hover { background-color: #42a5f5; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
        params_scroll.setWidgetResizable(True)
        params_scroll.setWidget(self.params_group)
        
        layout.addWidget(params_scroll)
        
        # Barre de progression avec style moderne
        progress_group = QGroupBox("Progression")
        progress_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        progress_inner_layout = QVBoxLayout(progress_group)
        progress_inner_layout.setContentsMargins(15, 15, 15, 15)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; height: 20px; text-align: center; }"
            "QProgressBar::chunk { background-color: #42a5f5; border-radius: 3px; }"
        )
        
        self.progress_status = QLabel("Prêt à exécuter le test")
        self.progress_status.setStyleSheet("color: #e0e0e0; font-weight: bold; margin-top: 5px;")
        
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status, 0, Qt.AlignmentFlag.AlignCenter)
        
        progress_inner_layout.addLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Zone de résultats avec style moderne amélioré
        results_group = QGroupBox("Résultats du test")
        results_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(15, 15, 15, 15)
        
        result_label_layout = QHBoxLayout()
        
        result_label = QLabel("Réponse de l'API:")
        result_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        result_label_layout.addWidget(result_label)
        
        result_label_layout.addStretch()
        
        self.copy_button = QPushButton("Copier")
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: white; padding: 4px 10px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #444444; }"
        )
        self.copy_button.clicked.connect(self._copy_results)
        
        result_label_layout.addWidget(self.copy_button)
        
        results_layout.addLayout(result_label_layout)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #444444; border-radius: 4px; padding: 10px; font-family: 'Consolas', 'Courier New', monospace; }"
        )
        self.result_text.setMinimumHeight(250)
        results_layout.addWidget(self.result_text)
        
        layout.addWidget(results_group, 1)  # 1 = stretch factor pour que les résultats prennent plus de place
        
        # Boutons avec style moderne
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: #252526; border-radius: 6px; padding: 10px;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 5, 10, 5)
        
        button_layout.addStretch(1)
        
        self.test_button = QPushButton("Exécuter le test")
        self.test_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.test_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.test_button.setStyleSheet(
            "QPushButton { background-color: #4caf50; color: white; font-weight: bold; padding: 8px 20px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #66bb6a; }"
        )
        self.test_button.clicked.connect(self._run_test)
        
        self.clear_button = QPushButton("Effacer les résultats")
        self.clear_button.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.setStyleSheet(
            "QPushButton { background-color: #ff9800; color: white; padding: 8px 20px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #ffb74d; }"
        )
        self.clear_button.clicked.connect(lambda: self.result_text.clear())
        
        self.close_button = QPushButton("Fermer")
        self.close_button.setIcon(QIcon.fromTheme("window-close"))
        self.close_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_button.setStyleSheet(
            "QPushButton { background-color: #757575; color: white; padding: 8px 20px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #9e9e9e; }"
        )
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.close_button)
        
        layout.addWidget(button_frame)
        
        # Initialiser la première API
        if self.api_combo.count() > 0:
            self._on_api_changed(0)
    
    def _populate_api_combo(self):
        """Remplit le combo avec les APIs disponibles"""
        if not self.api_manager:
            return
            
        apis = self.api_manager.get_apis()
        enabled_apis = {}
        
        # Ne montrer que les APIs activées
        for api_name, api_instance in apis.items():
            if api_instance and hasattr(api_instance, "enabled") and api_instance.enabled:
                enabled_apis[api_name] = api_instance
        
        for api_name in sorted(enabled_apis.keys()):
            self.api_combo.addItem(api_name)
    
    def _on_api_changed(self, index):
        """Gère le changement d'API"""
        if index < 0 or not self.api_manager:
            return
            
        api_name = self.api_combo.currentText()
        api = self.api_manager.get_api(api_name)
        
        if not api:
            return
            
        # Trouver les méthodes disponibles
        self.method_combo.clear()
        
        # Filtrer les méthodes qui ne sont pas des méthodes privées ou spéciales
        methods = [method for method in dir(api) 
                  if callable(getattr(api, method)) and 
                  not method.startswith('_')]
        
        for method in sorted(methods):
            self.method_combo.addItem(method)
            
        # Mettre à jour les paramètres
        if self.method_combo.count() > 0:
            self._on_method_changed(0)
    
    def _on_method_changed(self, index):
        """Gère le changement de méthode"""
        if index < 0 or not self.api_manager:
            return
            
        api_name = self.api_combo.currentText()
        method_name = self.method_combo.currentText()
        
        api = self.api_manager.get_api(api_name)
        
        if not api or not method_name:
            return
            
        # Effacer les paramètres existants
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        
        # Obtenir les informations sur la méthode
        method = getattr(api, method_name)
        
        try:
            # Tenter d'obtenir la signature de la méthode
            import inspect
            sig = inspect.signature(method)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                # Créer un widget pour chaque paramètre
                if param.default is inspect.Parameter.empty:
                    # Paramètre obligatoire
                    line_edit = QLineEdit()
                    self.params_layout.addRow(f"{param_name}:", line_edit)
                else:
                    # Paramètre optionnel
                    line_edit = QLineEdit()
                    line_edit.setPlaceholder(f"Optionnel (défaut: {param.default})")
                    self.params_layout.addRow(f"{param_name} (opt):", line_edit)
        except Exception as e:
            # Si on ne peut pas obtenir la signature, ajouter un éditeur de paramètres générique
            self.logger.warning(f"Impossible d'obtenir la signature de {method_name}: {e}")
            
            param_edit = QTextEdit()
            param_edit.setPlaceholderText("Entrez les paramètres au format JSON:\n{\n    \"param1\": \"valeur1\",\n    \"param2\": 123\n}")
            param_edit.setMaximumHeight(150)
            
            self.params_layout.addRow("Paramètres JSON:", param_edit)
    
    def _get_params(self):
        """Récupère les paramètres de l'interface utilisateur"""
        params = {}
        
        # Vérifier s'il y a un éditeur JSON
        if self.params_layout.rowCount() == 1:
            label_item = self.params_layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
            if label_item and label_item.widget().text() == "Paramètres JSON:":
                field_item = self.params_layout.itemAt(0, QFormLayout.ItemRole.FieldRole)
                if field_item and isinstance(field_item.widget(), QTextEdit):
                    json_text = field_item.widget().toPlainText().strip()
                    if json_text:
                        try:
                            return json.loads(json_text)
                        except json.JSONDecodeError as e:
                            QMessageBox.warning(self, "Erreur JSON", f"Format JSON invalide: {e}")
                            return None
                    return {}
        
        # Récupérer les paramètres des champs individuels
        for i in range(self.params_layout.rowCount()):
            label_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.params_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            
            if not label_item or not field_item:
                continue
                
            label = label_item.widget().text()
            field = field_item.widget()
            
            # Extraire le nom du paramètre du label
            param_name = label.split(":")[0].strip()
            if param_name.endswith(" (opt)"):
                param_name = param_name[:-6]
                
            # Récupérer la valeur
            if isinstance(field, QLineEdit):
                value = field.text().strip()
                if value:
                    # Essayer de convertir en nombre ou booléen si possible
                    if value.lower() == "true":
                        params[param_name] = True
                    elif value.lower() == "false":
                        params[param_name] = False
                    else:
                        try:
                            # Essayer de convertir en entier
                            params[param_name] = int(value)
                        except ValueError:
                            try:
                                # Essayer de convertir en float
                                params[param_name] = float(value)
                            except ValueError:
                                # Conserver comme chaîne
                                params[param_name] = value
            
        return params
    
    def _run_test(self):
        """Exécute le test d'API"""
        if not self.api_manager:
            QMessageBox.warning(self, "Erreur", "Gestionnaire d'API non initialisé")
            return
            
        api_name = self.api_combo.currentText()
        method_name = self.method_combo.currentText()
        
        if not api_name or not method_name:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une API et une méthode")
            return
            
        # Obtenir les paramètres
        params = self._get_params()
        if params is None:  # Erreur dans le format JSON
            return
        
        # Enregistrer le temps de début du test
        self.test_start_time = time.time()
            
        # Préparer l'interface
        self.progress_bar.setValue(0)
        self.progress_status.setText("Démarrage...")
        self.result_text.clear()
        self.test_button.setEnabled(False)
        
        # Animation de la barre de progression pour les tests longs
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._animate_progress)
        self.progress_timer.start(100)  # Mise à jour toutes les 100ms
        
        # Lancer le test en arrière-plan
        self.test_worker = ApiTestWorker(self.api_manager, api_name, method_name, params)
        self.test_worker.progress.connect(self._update_progress)
        self.test_worker.finished.connect(self._test_finished)
        self.test_worker.start()
    
    def _update_progress(self, value, message):
        """Met à jour la barre de progression"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
            
        self.progress_bar.setValue(value)
        self.progress_status.setText(message)
    
    def _animate_progress(self):
        """Anime la barre de progression pour les tests longs"""
        current_value = self.progress_bar.value()
        if current_value < 95:  # Limite à 95% pour indiquer que ce n'est pas terminé
            # Progression plus lente au fur et à mesure qu'on avance
            increment = max(1, 5 - current_value // 20)
            self.progress_bar.setValue(current_value + increment)
    
    def _test_finished(self, success, message, result):
        """Gère la fin du test"""
        self.test_button.setEnabled(True)
        
        # Arrêter l'animation de la barre de progression
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        # Calculer le temps d'exécution
        elapsed_time = time.time() - self.test_start_time if hasattr(self, 'test_start_time') else 0
        time_info = f"Temps d'exécution: {elapsed_time:.2f} secondes"
        
        # Effacer les résultats précédents et reset le style
        self.result_text.clear()
        self.result_text.setStyleSheet("")
        
        # Style pour l'entête du résultat
        if success:
            status_html = f'<div style="background-color: #1b5e20; color: white; padding: 10px; border-radius: 4px; margin-bottom: 10px;">'
            status_html += f'<span style="font-weight: bold; font-size: 14px;">✅ Test réussi</span><br/>'
            status_html += f'<span>{message}</span><br/>'
            status_html += f'<span style="font-size: 12px;">{time_info}</span>'
            status_html += '</div>'
            self.progress_status.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            status_html = f'<div style="background-color: #b71c1c; color: white; padding: 10px; border-radius: 4px; margin-bottom: 10px;">'
            status_html += f'<span style="font-weight: bold; font-size: 14px;">❌ Test échoué</span><br/>'
            status_html += f'<span>{message}</span><br/>'
            status_html += f'<span style="font-size: 12px;">{time_info}</span>'
            status_html += '</div>'
            self.progress_status.setStyleSheet("color: #f44336; font-weight: bold;")
        
        self.result_text.insertHtml(status_html)
        self.result_text.append("")
        
        # Afficher les résultats avec coloration syntaxique
        if isinstance(result, str):
            # Afficher les détails d'erreur ou le texte simple
            self.result_text.append(result)
        else:
            # Convertir en JSON pour une meilleure lisibilité avec coloration syntaxique
            try:
                formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
                highlighted_html = self._highlight_json(formatted_result)
                self.result_text.insertHtml(highlighted_html)
            except (TypeError, ValueError):
                # Si la conversion JSON échoue, afficher la représentation string
                self.result_text.append(str(result))
        
        # Remettre le curseur au début
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.result_text.setTextCursor(cursor)

    def _highlight_json(self, json_str):
        """Convertit le texte JSON en HTML avec coloration syntaxique"""
        # Échapper les caractères spéciaux HTML
        json_str = json_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Préparer le HTML pour les blocs de code avec style monospace
        html = ['<pre style="font-family: Consolas, \'Courier New\', monospace; margin: 0; padding: 0;">']
        
        # Analyse caractère par caractère
        in_string = False
        in_property = False
        in_number = False
        escape_next = False
        
        for i, char in enumerate(json_str):
            # Gestion des échappements
            if escape_next:
                html.append(char)
                escape_next = False
                continue
                
            if char == '\\' and in_string:
                html.append(char)
                escape_next = True
                continue
            
            # Détection des chaînes
            if char == '"':
                if not in_string:
                    # Début d'une chaîne
                    in_string = True
                    # Vérifier si c'est une propriété (clé) ou une valeur
                    i_next = i + 1
                    while i_next < len(json_str) and json_str[i_next].isspace():
                        i_next += 1
                    in_property = i_next < len(json_str) and json_str[i_next] == ':'
                    
                    if in_property:
                        html.append('<span style="color: #9cdcfe;">"')
                    else:
                        html.append('<span style="color: #ce9178;">"')
                else:
                    # Fin d'une chaîne
                    html.append('"</span>')
                    in_string = False
                    in_property = False
                continue
            
            # Détection des nombres
            if not in_string and (char.isdigit() or char == '-' or char == '.'):
                if not in_number and (char.isdigit() or char == '-'):
                    in_number = True
                    html.append('<span style="color: #b5cea8;">')
                html.append(char)
                # Vérifier si le prochain caractère n'est pas un chiffre (fin du nombre)
                if i+1 < len(json_str) and not (json_str[i+1].isdigit() or json_str[i+1] == '.'):
                    html.append('</span>')
                    in_number = False
                continue
            
            # Si nous sommes dans une chaîne ou un nombre, ajouter simplement le caractère
            if in_string or in_number:
                html.append(char)
                continue
            
            # Mots-clés et symboles
            if char in '{}':
                html.append(f'<span style="color: #d4d4d4;">{char}</span>')
            elif char in '[]':
                html.append(f'<span style="color: #d4d4d4;">{char}</span>')
            elif char == ':':
                html.append(f'<span style="color: #d4d4d4;">{char}</span>')
            elif char == ',':
                html.append(f'<span style="color: #d4d4d4;">{char}</span>')
            elif json_str[i:i+4] == 'true':
                html.append('<span style="color: #569cd6;">true</span>')
                # Skip the next 3 characters as we've already processed them
                i += 3
            elif json_str[i:i+5] == 'false':
                html.append('<span style="color: #569cd6;">false</span>')
                # Skip the next 4 characters
                i += 4
            elif json_str[i:i+4] == 'null':
                html.append('<span style="color: #569cd6;">null</span>')
                # Skip the next 3 characters
                i += 3
            else:
                html.append(char)
        
        html.append('</pre>')
        return ''.join(html)
    
    def _copy_results(self):
        """Copie les résultats du test dans le presse-papiers"""
        text = self.result_text.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            
            # Feedback visuel temporaire
            original_text = self.copy_button.text()
            self.copy_button.setText("Copié!")
            self.copy_button.setStyleSheet(
                "QPushButton { background-color: #4caf50; color: white; padding: 4px 10px; border-radius: 3px; }"
                "QPushButton:hover { background-color: #66bb6a; }"
            )
            
            # Réinitialiser après un délai
            QTimer.singleShot(1500, lambda: [
                self.copy_button.setText(original_text),
                self.copy_button.setStyleSheet(
                    "QPushButton { background-color: #333333; color: white; padding: 4px 10px; border-radius: 3px; }"
                    "QPushButton:hover { background-color: #444444; }"
                )
            ])

def show_api_test_dialog(api_manager, parent=None):
    """
    Affiche le dialogue de test des APIs
    
    Args:
        api_manager: Gestionnaire d'APIs
        parent: Widget parent
    """
    dialog = APITestDialog(api_manager, parent)
    dialog.exec()
