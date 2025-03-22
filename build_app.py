#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de construction de l'application Polyad.app
Utilise py2app pour créer une application macOS native avec intégration d'APIs généralistes
"""
import os
import sys
import json
import shutil
from setuptools import setup

APP_NAME = "Polyad"
VERSION = "2.0.0"
APP_ICON = "polyad_icon.icns"  # Sera créé par le script

# Liste des APIs intégrées
INTEGRATED_APIS = {
    "huggingface": "Accès à des milliers de modèles ML",
    "wikipedia": "Recherche d'informations vérifiées",
    "openmeteo": "Données météorologiques",
    "newsapi": "Actualités en temps réel",
    "translation": "Support multilingue",
    "ocr": "Reconnaissance de texte dans les images",
    "textanalysis": "Analyse sémantique avancée",
    "meilisearch": "Recherche vectorielle",
    "slack": "Intégration de messagerie",
    "github": "Gestion de code",
    "calendar": "Planification",
    "notion": "Base de connaissances structurée"
}

# Générer le fichier de configuration des APIs
api_config_path = "config/api/apis.json"
os.makedirs(os.path.dirname(api_config_path), exist_ok=True)

if not os.path.exists(api_config_path):
    api_config = {
        "version": VERSION,
        "apis": {
            name: {
                "description": desc,
                "enabled": True,
                "api_key": "",
                "base_url": "",
                "rate_limit": 100,
                "cache_ttl": 3600
            } for name, desc in INTEGRATED_APIS.items()
        },
        "global_settings": {
            "use_cache": True,
            "default_ttl": 3600,
            "load_balancing": True,
            "retry_attempts": 3,
            "timeout": 30
        }
    }
    
    with open(api_config_path, 'w') as f:
        json.dump(api_config, f, indent=2)
    print(f"Configuration API créée: {api_config_path}")

# Créer une icône simple si elle n'existe pas
if not os.path.exists(APP_ICON):
    try:
        import subprocess
        
        # Créer un SVG plus moderne pour l'icône
        with open("polyad_icon.svg", "w") as f:
            f.write('''<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3498db;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8e44ad;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="220" ry="220" fill="url(#grad1)" />
  <circle cx="512" cy="512" r="350" fill="rgba(255,255,255,0.1)" />
  <circle cx="512" cy="512" r="250" fill="rgba(255,255,255,0.15)" />
  <text x="512" y="550" font-family="Arial" font-size="300" text-anchor="middle" fill="white" font-weight="bold">P</text>
</svg>''')
        
        # Utiliser cairosvg si disponible, sinon utiliser sips
        try:
            import cairosvg
            cairosvg.svg2png(url="polyad_icon.svg", write_to="polyad_icon.png", output_width=1024, output_height=1024)
        except ImportError:
            # Fallback à convert si disponible
            try:
                subprocess.run(["convert", "polyad_icon.svg", "polyad_icon.png"])
            except:
                print("Aucun outil de conversion SVG trouvé - création d'une icône minimaliste")
                # Créer une icône PNG minimaliste si aucune méthode n'est disponible
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (1024, 1024), color = (52, 152, 219))
                d = ImageDraw.Draw(img)
                d.ellipse((212, 212, 812, 812), fill=(41, 128, 185))
                try:
                    font = ImageFont.truetype("Arial.ttf", 400)
                except:
                    font = ImageFont.load_default()
                d.text((512, 512), "P", font=font, fill=(255, 255, 255), anchor="mm")
                img.save('polyad_icon.png')
        
        # Créer un dossier iconset
        os.makedirs("polyad.iconset", exist_ok=True)
        
        # Génération des tailles d'icônes
        icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in icon_sizes:
            if size <= 1024:
                subprocess.run([
                    "sips", "-z", str(size), str(size), 
                    "polyad_icon.png", "--out", 
                    f"polyad.iconset/icon_{size}x{size}.png"
                ])
                # Version @2x pour les tailles qui le permettent
                if size * 2 <= 1024:
                    subprocess.run([
                        "sips", "-z", str(size*2), str(size*2), 
                        "polyad_icon.png", "--out", 
                        f"polyad.iconset/icon_{size}x{size}@2x.png"
                    ])
        
        # Créer l'icône ICNS
        subprocess.run(["iconutil", "-c", "icns", "polyad.iconset"])
        
        # Nettoyer
        shutil.rmtree("polyad.iconset")
        os.remove("polyad_icon.svg")
        os.remove("polyad_icon.png")
        print("Icône créée avec succès!")
    except Exception as e:
        print(f"Erreur lors de la création de l'icône: {e}")
        print("L'application sera construite sans icône personnalisée.")

# Configuration pour py2app
setup(
    name=APP_NAME,
    app=["polyad_app.py"],
    version=VERSION,
    description="Application macOS native pour Polyad avec intégration d'APIs généralistes",
    author="Polyad Team",
    author_email="contact@polyad.ai",
    url="https://polyad.ai",
    options={
        "py2app": {
            "argv_emulation": True,
            "iconfile": APP_ICON if os.path.exists(APP_ICON) else None,
            "plist": {
                "CFBundleName": APP_NAME,
                "CFBundleDisplayName": APP_NAME,
                "CFBundleGetInfoString": f"Polyad {VERSION} - Assistant IA généraliste, (c) 2025",
                "CFBundleIdentifier": "com.polyad.app",
                "CFBundleVersion": VERSION,
                "CFBundleShortVersionString": VERSION,
                "LSMinimumSystemVersion": "10.14",
                "NSHumanReadableCopyright": "Copyright © 2025 Polyad, Tous droits réservés.",
                "NSHighResolutionCapable": True,
                "NSAppTransportSecurity": {
                    "NSAllowsArbitraryLoads": True
                },
                "LSApplicationCategoryType": "public.app-category.productivity",
                "LSUIElement": False,
            },
            "packages": ["PyQt6", "requests", "docker", "json", "urllib3", "chardet", "certifi"],
            "includes": [
                "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.QtWebEngineWidgets",
                "json", "ssl", "uuid", "logging", "datetime", "hashlib", "hmac"
            ],
            "excludes": ["tkinter", "matplotlib", "pandas", "numpy", "scipy"],
            "frameworks": [],
            "resources": [
                "docker-compose.yml",
                ".env.production",
                "config",
                "docs",
                "ui"
            ],
        }
    },
    data_files=[
        ('config/api', ['config/api/apis.json']),
    ],
    setup_requires=["py2app"],
    install_requires=[
        "PyQt6>=6.4.0",
        "PyQt6-WebEngine>=6.4.0",
        "requests>=2.27.0",
        "docker>=6.0.0",
        "urllib3>=1.26.0",
        "pyyaml>=6.0",
        "meilisearch>=0.21.0",
        "huggingface-hub>=0.10.0",
        "wikipedia-api>=0.5.8",
        "newsapi-python>=0.2.6",
        "googletrans>=4.0.0-rc1",
        "pyocr>=0.8.0",
        "slackclient>=2.9.3",
        "pygithub>=1.55",
        "notion-client>=1.0.0"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: MacOS X",
        "Environment :: MacOS X :: Cocoa",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
)

print("--------------------------------------------")
print(f"Application {APP_NAME}.app créée avec succès!")
print("--------------------------------------------")
print("Pour installer les dépendances et construire l'application, exécutez:")
print("  pip install -r requirements-app.txt")
print("  python build_app.py py2app")
print("\nPour construire en mode développement (plus rapide):")
print("  python build_app.py py2app -A")
print("--------------------------------------------")
