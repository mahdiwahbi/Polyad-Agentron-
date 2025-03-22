#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface de configuration des APIs pour Polyad
Permet de configurer les APIs externes intégrées
"""
import os
import json
import logging
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QLineEdit, QCheckBox, QSpinBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFormLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QIcon, QFont

class APIConfigDialog(QDialog):
    """
    Dialogue de configuration des APIs pour Polyad
    Permet à l'utilisateur de:
    - Activer/désactiver des APIs
    - Configurer les clés API
    - Définir les URLs de base
    - Configurer les paramètres de mise en cache
    """
    
    # Signal émis lorsque la configuration est modifiée
    config_changed = pyqtSignal()
    
    def __init__(self, api_manager=None, parent=None):
        """
        Initialise le dialogue de configuration
        
        Args:
            api_manager: Gestionnaire d'API
            parent: Widget parent
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.api_manager = api_manager
        self.config_path = api_manager.config_path if api_manager else os.path.join("config", "api", "apis.json")
        self.config = self._load_config()
        
        self.setWindowTitle("Configuration des APIs")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(QIcon.fromTheme("preferences-system"))
        
        # Application d'un style moderne
        self._setup_style()
        
        self._init_ui()
    
    def _load_config(self):
        """Charge la configuration des APIs"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Fichier de configuration {self.config_path} non trouvé")
                return {"apis": {}, "global_settings": {}}
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return {"apis": {}, "global_settings": {}}
    
    def _save_config(self):
        """Sauvegarde la configuration des APIs"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration sauvegardée dans {self.config_path}")
            
            # Si le gestionnaire d'API est disponible, recharger la configuration
            if self.api_manager:
                self.api_manager._load_config()
                self.api_manager._initialize_apis()
            
            # Émettre le signal de changement de configuration
            self.config_changed.emit()
            
            QMessageBox.information(self, "Configuration sauvegardée", 
                                   "La configuration des APIs a été sauvegardée avec succès.")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
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
            QLineEdit, QSpinBox { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 4px; }
            QLineEdit:focus, QSpinBox:focus { border: 1px solid #42a5f5; }
            QCheckBox { color: #e0e0e0; }
            QCheckBox::indicator { width: 15px; height: 15px; }
            QCheckBox::indicator:unchecked { background-color: #333333; border: 1px solid #555555; border-radius: 3px; }
            QCheckBox::indicator:checked { background-color: #42a5f5; border: 1px solid #42a5f5; border-radius: 3px; }
            QTableWidget { background-color: #252526; alternate-background-color: #2d2d30; color: white; gridline-color: #444444; }
            QTableWidget::item:selected { background-color: #42a5f5; }
            QHeaderView::section { background-color: #333333; color: white; padding: 5px; border: none; }
            QScrollArea { background-color: #1e1e1e; border: none; }
            QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; }
            QFormLayout { spacing: 10px; }
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
        
        title_label = QLabel("Configuration des intégrations API")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        desc_label = QLabel("Activez, configurez et personnalisez les intégrations API pour votre environnement.")
        desc_label.setStyleSheet("color: #e0e0e0;")
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header_frame)
        
        # Créer un widget d'onglets avec style moderne
        self.tab_widget = QTabWidget()
        
        # Onglet pour les APIs
        self.api_tab = QWidget()
        self.api_tab_layout = QVBoxLayout(self.api_tab)
        self.api_tab_layout.setContentsMargins(10, 15, 10, 10)
        self.api_tab_layout.setSpacing(10)
        
        # Barre de recherche pour filtrer les APIs
        search_layout = QHBoxLayout()
        search_label = QLabel("Rechercher:")
        search_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Filtrer les APIs par nom ou description...")
        search_input.setClearButtonEnabled(True)
        search_input.setStyleSheet(
            "QLineEdit { background-color: #333333; color: white; border: 1px solid #555555; border-radius: 4px; padding: 6px; }"
            "QLineEdit:focus { border: 1px solid #42a5f5; }"
        )
        search_input.textChanged.connect(self._filter_api_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input, 1)
        self.api_tab_layout.addLayout(search_layout)
        
        # Créer un tableau pour les APIs avec style amélioré
        self.api_table = QTableWidget()
        self.api_table.setColumnCount(5)
        self.api_table.setHorizontalHeaderLabels(["API", "Description", "Activée", "Clé API", "Limite de taux"])
        self.api_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.api_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.api_table.verticalHeader().setVisible(False)
        self.api_table.setAlternatingRowColors(True)
        self.api_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.api_table.horizontalHeader().setStyleSheet("QHeaderView::section { font-weight: bold; }")
        
        # Remplir le tableau avec les APIs
        self._populate_api_table()
        
        self.api_tab_layout.addWidget(self.api_table)
        
        # Onglet pour les paramètres globaux avec style amélioré
        self.global_tab = QWidget()
        self.global_tab_layout = QVBoxLayout(self.global_tab)
        self.global_tab_layout.setContentsMargins(15, 15, 15, 15)
        self.global_tab_layout.setSpacing(15)
        
        # Groupe de paramètres pour le cache
        cache_group = QGroupBox("Paramètres de cache")
        cache_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        cache_layout = QFormLayout(cache_group)
        cache_layout.setContentsMargins(15, 15, 15, 15)
        cache_layout.setSpacing(10)
        
        # Widget de cache
        self.cache_checkbox = QCheckBox("Utiliser le cache")
        self.cache_checkbox.setChecked(self.config.get("global_settings", {}).get("use_cache", True))
        
        self.ttl_spinbox = QSpinBox()
        self.ttl_spinbox.setRange(60, 86400)
        self.ttl_spinbox.setValue(self.config.get("global_settings", {}).get("default_ttl", 3600))
        self.ttl_spinbox.setSuffix(" secondes")
        
        # Ajouter au groupe de cache
        cache_layout.addRow("Activer:", self.cache_checkbox)
        cache_layout.addRow("Durée de vie par défaut:", self.ttl_spinbox)
        
        # Groupe de paramètres pour l'équilibrage de charge
        lb_group = QGroupBox("Équilibrage de charge et performances")
        lb_group.setStyleSheet(
            "QGroupBox { background-color: #252526; border: 1px solid #333333; border-radius: 4px; margin-top: 20px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; color: #42a5f5; padding: 0 5px; background-color: #252526; font-weight: bold; }"
        )
        lb_layout = QFormLayout(lb_group)
        lb_layout.setContentsMargins(15, 15, 15, 15)
        lb_layout.setSpacing(10)
        
        # Widgets d'équilibrage de charge
        self.load_balancing_checkbox = QCheckBox("Activer l'équilibrage de charge")
        self.load_balancing_checkbox.setChecked(self.config.get("global_settings", {}).get("load_balancing", True))
        
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setRange(1, 10)
        self.retry_spinbox.setValue(self.config.get("global_settings", {}).get("retry_attempts", 3))
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(5, 300)
        self.timeout_spinbox.setValue(self.config.get("global_settings", {}).get("timeout", 30))
        self.timeout_spinbox.setSuffix(" secondes")
        
        # Ajouter au groupe d'équilibrage
        lb_layout.addRow("Activer:", self.load_balancing_checkbox)
        lb_layout.addRow("Tentatives de réessai:", self.retry_spinbox)
        lb_layout.addRow("Délai d'attente:", self.timeout_spinbox)
        
        # Ajouter les groupes au layout principal
        self.global_tab_layout.addWidget(cache_group)
        self.global_tab_layout.addWidget(lb_group)
        self.global_tab_layout.addStretch(1)
        
        # Ajouter les widgets au layout
        self.global_tab_layout.addRow("Cache:", self.cache_checkbox)
        self.global_tab_layout.addRow("Durée de vie du cache:", self.ttl_spinbox)
        self.global_tab_layout.addRow("Équilibrage de charge:", self.load_balancing_checkbox)
        self.global_tab_layout.addRow("Tentatives de réessai:", self.retry_spinbox)
        self.global_tab_layout.addRow("Délai d'attente:", self.timeout_spinbox)
        
        # Onglet pour les informations sur les APIs
        self.info_tab = QWidget()
        self.info_tab_layout = QVBoxLayout(self.info_tab)
        
        # Créer une zone de défilement pour les informations sur les APIs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Ajouter les informations sur chaque API
        api_infos = {
            "huggingface": {
                "name": "Hugging Face",
                "description": "Accès à des milliers de modèles ML",
                "url": "https://huggingface.co/",
                "doc_url": "https://huggingface.co/docs/api-inference/index",
                "free_tier": "30K requêtes/mois",
                "features": [
                    "Génération de texte",
                    "Classification de texte",
                    "Reconnaissance d'entités nommées",
                    "Réponse aux questions",
                    "Résumé de texte",
                    "Traduction"
                ]
            },
            "wikipedia": {
                "name": "Wikipedia",
                "description": "Recherche d'informations vérifiées",
                "url": "https://www.wikipedia.org/",
                "doc_url": "https://www.mediawiki.org/wiki/API:Main_page",
                "free_tier": "Illimité, usage raisonnable",
                "features": [
                    "Recherche d'articles",
                    "Récupération de résumés",
                    "Information sur les pages",
                    "Récupération d'images"
                ]
            },
            "openmeteo": {
                "name": "Open-Meteo",
                "description": "Données météorologiques",
                "url": "https://open-meteo.com/",
                "doc_url": "https://open-meteo.com/en/docs",
                "free_tier": "10000 requêtes/jour",
                "features": [
                    "Prévisions météorologiques",
                    "Données historiques",
                    "Données climatiques"
                ]
            },
            "newsapi": {
                "name": "News API",
                "description": "Actualités en temps réel",
                "url": "https://newsapi.org/",
                "doc_url": "https://newsapi.org/docs",
                "free_tier": "100 requêtes/jour",
                "features": [
                    "Titres principaux",
                    "Recherche d'articles",
                    "Filtrage par source, pays, catégorie"
                ]
            },
            "translation": {
                "name": "LibreTranslate",
                "description": "Support multilingue",
                "url": "https://libretranslate.com/",
                "doc_url": "https://libretranslate.com/docs/",
                "free_tier": "Illimité (auto-hébergement)",
                "features": [
                    "Traduction de texte",
                    "Détection de langue",
                    "Support de plus de 30 langues"
                ]
            },
            "ocr": {
                "name": "OCR.space",
                "description": "Reconnaissance de texte dans les images",
                "url": "https://ocr.space/",
                "doc_url": "https://ocr.space/OCRAPI",
                "free_tier": "25000 requêtes/mois",
                "features": [
                    "Extraction de texte depuis des images",
                    "Support de nombreuses langues",
                    "Reconnaissance de texte manuscrit"
                ]
            },
            "textanalysis": {
                "name": "Text Analysis API",
                "description": "Analyse sémantique avancée",
                "url": "https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-text-analytics/",
                "doc_url": "https://docs.microsoft.com/en-us/azure/cognitive-services/text-analytics/",
                "free_tier": "5000 transactions/mois",
                "features": [
                    "Analyse de sentiment",
                    "Extraction d'entités",
                    "Détection de la langue",
                    "Extraction de phrases clés"
                ]
            },
            "meilisearch": {
                "name": "Meilisearch",
                "description": "Recherche vectorielle",
                "url": "https://www.meilisearch.com/",
                "doc_url": "https://docs.meilisearch.com/",
                "free_tier": "Illimité (auto-hébergement)",
                "features": [
                    "Recherche full-text",
                    "Recherche vectorielle",
                    "Typo-tolérance",
                    "Filtres et facettes"
                ]
            },
            "slack": {
                "name": "Slack",
                "description": "Intégration de messagerie",
                "url": "https://slack.com/",
                "doc_url": "https://api.slack.com/",
                "free_tier": "Illimité avec auth",
                "features": [
                    "Envoi de messages",
                    "Création de canaux",
                    "Gestion des utilisateurs",
                    "Webhooks"
                ]
            },
            "github": {
                "name": "GitHub",
                "description": "Gestion de code",
                "url": "https://github.com/",
                "doc_url": "https://docs.github.com/en/rest",
                "free_tier": "5000 requêtes/heure",
                "features": [
                    "Accès aux dépôts",
                    "Gestion des issues",
                    "Gestion des pull requests",
                    "Webhooks"
                ]
            },
            "calendar": {
                "name": "Google Calendar",
                "description": "Planification",
                "url": "https://calendar.google.com/",
                "doc_url": "https://developers.google.com/calendar",
                "free_tier": "1M requêtes/jour",
                "features": [
                    "Création d'événements",
                    "Récupération d'événements",
                    "Gestion des calendriers",
                    "Rappels"
                ]
            },
            "notion": {
                "name": "Notion",
                "description": "Base de connaissances structurée",
                "url": "https://www.notion.so/",
                "doc_url": "https://developers.notion.com/",
                "free_tier": "500 opérations/mois",
                "features": [
                    "Création de pages",
                    "Gestion de bases de données",
                    "Recherche",
                    "Filtrage"
                ]
            }
        }
        
        for api_id, info in api_infos.items():
            group_box = QGroupBox(info["name"])
            group_layout = QVBoxLayout()
            
            # Titre et description
            title_label = QLabel(f'<b>{info["name"]}</b>')
            title_label.setStyleSheet("font-size: 16px;")
            desc_label = QLabel(info["description"])
            desc_label.setWordWrap(True)
            
            # URLs
            url_label = QLabel(f'<a href="{info["url"]}">{info["url"]}</a>')
            url_label.setOpenExternalLinks(True)
            doc_url_label = QLabel(f'Documentation: <a href="{info["doc_url"]}">{info["doc_url"]}</a>')
            doc_url_label.setOpenExternalLinks(True)
            
            # Tier gratuit
            free_tier_label = QLabel(f'<b>Tier gratuit:</b> {info["free_tier"]}')
            
            # Fonctionnalités
            features_label = QLabel("<b>Fonctionnalités:</b>")
            features_text = "<ul>" + "".join([f"<li>{feature}</li>" for feature in info["features"]]) + "</ul>"
            features_content = QLabel(features_text)
            features_content.setWordWrap(True)
            
            # Ajouter au layout du groupe
            group_layout.addWidget(title_label)
            group_layout.addWidget(desc_label)
            group_layout.addWidget(url_label)
            group_layout.addWidget(doc_url_label)
            group_layout.addWidget(free_tier_label)
            group_layout.addWidget(features_label)
            group_layout.addWidget(features_content)
            
            group_box.setLayout(group_layout)
            scroll_layout.addWidget(group_box)
        
        scroll_area.setWidget(scroll_widget)
        self.info_tab_layout.addWidget(scroll_area)
        
        # Ajouter les onglets au widget d'onglets
        self.tab_widget.addTab(self.api_tab, "APIs")
        self.tab_widget.addTab(self.global_tab, "Paramètres globaux")
        self.tab_widget.addTab(self.info_tab, "Informations")
        
        layout.addWidget(self.tab_widget)
        
        # Boutons de confirmation avec style amélioré
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: #252526; border-radius: 6px; padding: 10px;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 5, 10, 5)
        
        button_layout.addStretch(1)
        
        self.save_button = QPushButton("Enregistrer")
        self.save_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_button.setStyleSheet(
            "QPushButton { background-color: #4caf50; color: white; font-weight: bold; padding: 8px 20px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #66bb6a; }"
        )
        self.save_button.clicked.connect(self._on_save)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setIcon(QIcon.fromTheme("dialog-cancel"))
        self.cancel_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_button.setStyleSheet(
            "QPushButton { background-color: #757575; color: white; padding: 8px 20px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #9e9e9e; }"
        )
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addWidget(button_frame)
    
    def _populate_api_table(self):
        """Remplit le tableau avec les APIs configurées"""
        apis = self.config.get("apis", {})
        self.api_table.setRowCount(len(apis))
        
        for i, (api_name, api_config) in enumerate(apis.items()):
            # Nom de l'API
            name_item = QTableWidgetItem(api_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.api_table.setItem(i, 0, name_item)
            
            # Description
            desc_item = QTableWidgetItem(api_config.get("description", ""))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.api_table.setItem(i, 1, desc_item)
            
            # Activée
            enabled_checkbox = QTableWidgetItem()
            enabled_checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            enabled_checkbox.setCheckState(Qt.CheckState.Checked if api_config.get("enabled", True) else Qt.CheckState.Unchecked)
            self.api_table.setItem(i, 2, enabled_checkbox)
            
            # Clé API
            api_key_item = QTableWidgetItem(api_config.get("api_key", ""))
            self.api_table.setItem(i, 3, api_key_item)
            
            # Limite de taux
            rate_limit_item = QTableWidgetItem(str(api_config.get("rate_limit", 100)))
            self.api_table.setItem(i, 4, rate_limit_item)
    
    def _on_save(self):
        """Gère l'événement de sauvegarde"""
        # Mettre à jour la configuration des APIs
        apis = self.config.get("apis", {})
        for i in range(self.api_table.rowCount()):
            api_name = self.api_table.item(i, 0).text()
            
            # Mettre à jour l'état d'activation
            enabled = self.api_table.item(i, 2).checkState() == Qt.CheckState.Checked
            apis[api_name]["enabled"] = enabled
            
            # Mettre à jour la clé API
            api_key = self.api_table.item(i, 3).text()
            apis[api_name]["api_key"] = api_key
            
            # Mettre à jour la limite de taux
            try:
                rate_limit = int(self.api_table.item(i, 4).text())
                apis[api_name]["rate_limit"] = rate_limit
            except ValueError:
                pass
        
        # Mettre à jour les paramètres globaux
        self.config.setdefault("global_settings", {})
        self.config["global_settings"]["use_cache"] = self.cache_checkbox.isChecked()
        self.config["global_settings"]["default_ttl"] = self.ttl_spinbox.value()
        self.config["global_settings"]["load_balancing"] = self.load_balancing_checkbox.isChecked()
        self.config["global_settings"]["retry_attempts"] = self.retry_spinbox.value()
        self.config["global_settings"]["timeout"] = self.timeout_spinbox.value()
        
        # Sauvegarder la configuration
        if self._save_config():
            self.accept()

def show_api_config_dialog(api_manager, parent=None):
    """
    Affiche le dialogue de configuration des APIs
    
    Args:
        api_manager: Gestionnaire d'APIs
        parent: Widget parent
        
    Returns:
        bool: True si des modifications ont été apportées, False sinon
    """
    dialog = APIConfigDialog(api_manager, parent)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
