#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour sauvegarder et convertir le logo Polyad
"""
import os
from PIL import Image
import sys

def save_logo(input_path, output_path):
    """
    Convertit et sauvegarde le logo au format PNG
    """
    try:
        # Ouvrir l'image source
        with Image.open(input_path) as img:
            # Convertir en RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Redimensionner à 1024x1024 si nécessaire
            if img.size != (1024, 1024):
                img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            
            # Sauvegarder en PNG
            img.save(output_path, "PNG")
            print(f"Logo sauvegardé avec succès dans {output_path}")
            return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du logo: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: save_logo.py <chemin_image_source>")
        sys.exit(1)
    
    # Chemins des fichiers
    input_path = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "resources", "polyad_logo.png")
    
    # Créer le dossier resources si nécessaire
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sauvegarder le logo
    if save_logo(input_path, output_path):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
