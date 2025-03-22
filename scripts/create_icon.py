#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer l'icône de l'application Polyad
"""
import os
import sys
import shutil
import subprocess
from PIL import Image

def create_iconset(input_image_path, output_iconset_path):
    """
    Crée un ensemble d'icônes à partir d'une image source
    """
    # Créer le dossier iconset s'il n'existe pas
    os.makedirs(output_iconset_path, exist_ok=True)
    
    # Tailles d'icônes requises pour macOS
    icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # Ouvrir l'image source
    with Image.open(input_image_path) as img:
        # Convertir en RGBA si ce n'est pas déjà le cas
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Générer chaque taille d'icône
        for size in icon_sizes:
            if size <= 1024:
                # Redimensionner l'image
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Sauvegarder l'icône normale
                icon_path = os.path.join(output_iconset_path, f"icon_{size}x{size}.png")
                resized.save(icon_path, "PNG")
                
                # Sauvegarder la version @2x si possible
                if size * 2 <= 1024:
                    icon_2x_path = os.path.join(output_iconset_path, f"icon_{size}x{size}@2x.png")
                    img_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
                    img_2x.save(icon_2x_path, "PNG")

def main():
    # Chemins des fichiers
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    resources_dir = os.path.join(project_root, "resources")
    
    # Vérifier si le fichier icns existe déjà
    existing_icns = os.path.join(project_root, "polyad_icon.icns")
    if os.path.exists(existing_icns):
        print(f"Le fichier icône existe déjà: {existing_icns}")
        # Copier l'icône dans le dossier de l'application
        prepare_app_icon(existing_icns)
        return
        
    # Si l'icône n'existe pas, essayer de la créer à partir du logo
    input_image = os.path.join(resources_dir, "polyad_logo.png")
    iconset_path = os.path.join(project_root, "polyad.iconset")
    output_icns = os.path.join(project_root, "polyad_icon.icns")
    
    # Vérifier que l'image source existe
    if not os.path.exists(input_image):
        print(f"Erreur: L'image source n'existe pas: {input_image}")
        sys.exit(1)
    
    try:
        # Créer l'ensemble d'icônes
        create_iconset(input_image, iconset_path)
        
        # Convertir l'ensemble d'icônes en fichier .icns
        subprocess.run(["iconutil", "-c", "icns", iconset_path], check=True)
        
        # Déplacer le fichier .icns si nécessaire
        if os.path.exists("polyad.icns"):
            shutil.move("polyad.icns", output_icns)
        
        print(f"Icône créée avec succès: {output_icns}")
        
    except Exception as e:
        print(f"Erreur lors de la création de l'icône: {e}")
        sys.exit(1)
    finally:
        # Nettoyer le dossier iconset
        if os.path.exists(iconset_path):
            shutil.rmtree(iconset_path)

def prepare_app_icon(icns_path):
    """Prépare l'icône pour l'application en la copiant dans les dossiers nécessaires"""
    try:
        # Vérifier si le dossier dist existe
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        dist_dir = os.path.join(project_root, "dist")
        
        if os.path.exists(dist_dir):
            # Chercher le dossier Polyad.app
            app_dir = os.path.join(dist_dir, "Polyad.app")
            if os.path.exists(app_dir):
                # Chemin vers le dossier Resources de l'application
                resources_dir = os.path.join(app_dir, "Contents", "Resources")
                if os.path.exists(resources_dir):
                    # Copier l'icône dans le dossier Resources
                    icon_dest = os.path.join(resources_dir, "polyad_icon.icns")
                    shutil.copy2(icns_path, icon_dest)
                    print(f"Icône copiée dans l'application: {icon_dest}")
                    
                    # Mettre à jour le fichier Info.plist pour utiliser l'icône
                    info_plist = os.path.join(app_dir, "Contents", "Info.plist")
                    if os.path.exists(info_plist):
                        update_info_plist(info_plist)
                else:
                    print(f"Le dossier Resources n'existe pas: {resources_dir}")
            else:
                print(f"L'application Polyad.app n'existe pas: {app_dir}")
        else:
            print(f"Le dossier dist n'existe pas: {dist_dir}")
            print("Exécutez d'abord python build_app.py py2app pour construire l'application.")
    except Exception as e:
        print(f"Erreur lors de la préparation de l'icône: {e}")

def update_info_plist(plist_path):
    """Met à jour le fichier Info.plist pour utiliser l'icône"""
    try:
        # Utiliser plutil pour modifier le fichier plist
        subprocess.run([
            "defaults", "write", plist_path, 
            "CFBundleIconFile", "polyad_icon.icns"
        ], check=True)
        print(f"Fichier Info.plist mis à jour: {plist_path}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du fichier Info.plist: {e}")

if __name__ == "__main__":
    main()
