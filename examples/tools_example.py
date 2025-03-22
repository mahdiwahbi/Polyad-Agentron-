#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List

# Ajouter le répertoire parent au chemin d'importation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules Polyad
from tools import PolyadTools

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def display_result(title: str, result: Any):
    """
    Affiche un résultat de manière formatée
    
    Args:
        title: Titre du résultat
        result: Résultat à afficher
    """
    print(f"\n{title}:")
    
    if result is None:
        print("  Aucun résultat")
        return
    
    if isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, (dict, list)) and len(str(value)) > 100:
                print(f"  {key}: [Données complexes]")
            else:
                print(f"  {key}: {value}")
    elif isinstance(result, list):
        if not result:
            print("  Liste vide")
        elif len(result) > 5:
            for item in result[:3]:
                print(f"  - {item}")
            print(f"  ... et {len(result) - 3} autres éléments")
        else:
            for item in result:
                print(f"  - {item}")
    elif isinstance(result, str) and len(result) > 200:
        print(f"  {result[:200]}... [tronqué]")
    else:
        print(f"  {result}")

def main():
    """Fonction principale de démonstration"""
    print("Démarrage de la démonstration des outils Polyad...")
    
    # Créer une instance des outils
    tools = PolyadTools()
    
    try:
        # 1. Recherche web
        query = "Polyad AI agent architecture"
        display_result(f"1. Recherche web pour '{query}'", tools.web_search(query, max_results=3))
        
        # 2. Extraction d'informations d'une page web
        url = "https://github.com/langchain-ai/langchain"
        display_result(f"2. Extraction d'informations de '{url}'", tools.extract_from_url(url))
        
        # 3. Résumé de texte
        text = """
        L'intelligence artificielle (IA) est un domaine de l'informatique qui vise à créer des machines 
        capables de simuler l'intelligence humaine. Elle englobe plusieurs sous-domaines, notamment 
        l'apprentissage automatique (machine learning), le traitement du langage naturel, la vision par 
        ordinateur, et la robotique. L'apprentissage automatique, en particulier, a connu des avancées 
        significatives ces dernières années, notamment grâce aux réseaux de neurones profonds (deep learning).
        
        Les applications de l'IA sont nombreuses et touchent de nombreux secteurs : santé, finance, 
        transport, divertissement, etc. Dans la santé, par exemple, l'IA aide au diagnostic médical, 
        à la découverte de médicaments, et à la personnalisation des traitements. Dans la finance, 
        elle est utilisée pour la détection de fraudes, l'analyse de risques, et le trading algorithmique.
        
        Malgré ses nombreux avantages, l'IA soulève également des questions éthiques importantes concernant 
        la vie privée, la sécurité, l'emploi, et les biais algorithmiques. Il est donc crucial de développer 
        et d'utiliser l'IA de manière responsable, en tenant compte de ces enjeux.
        """
        display_result("3. Résumé de texte", tools.summarize_text(text))
        
        # 4. Analyse d'image (simulation)
        image_path = os.path.join(os.path.dirname(__file__), "sample_image.jpg")
        
        # Créer une image de test si elle n'existe pas
        if not os.path.exists(image_path):
            try:
                # Créer une image de test avec PIL
                from PIL import Image, ImageDraw, ImageFont
                
                # Créer une image vide
                img = Image.new('RGB', (400, 200), color=(73, 109, 137))
                
                # Dessiner du texte
                d = ImageDraw.Draw(img)
                d.text((10, 10), "Polyad Test Image", fill=(255, 255, 0))
                d.text((10, 50), "AI Agent Framework", fill=(255, 255, 0))
                d.rectangle([(50, 100), (350, 150)], outline=(255, 255, 255))
                
                # Sauvegarder l'image
                img.save(image_path)
                print(f"Image de test créée: {image_path}")
            except ImportError:
                print("PIL non disponible, impossible de créer l'image de test")
                image_path = None
        
        if image_path and os.path.exists(image_path):
            display_result("4. Analyse d'image", tools.analyze_image(image_path))
        else:
            print("\n4. Analyse d'image: Impossible - Image non disponible")
        
        # 5. Génération de texte
        prompt = "Écrivez un court poème sur l'intelligence artificielle et la créativité"
        display_result(f"5. Génération de texte pour '{prompt}'", tools.generate_text(prompt))
        
        # 6. Traduction
        text_to_translate = "L'intelligence artificielle transforme notre façon de travailler et de vivre."
        target_language = "en"  # Anglais
        display_result(f"6. Traduction vers '{target_language}'", 
                      tools.translate_text(text_to_translate, target_language))
        
        # 7. Extraction d'entités
        text_for_entities = """
        Apple Inc. a annoncé aujourd'hui le lancement de son nouveau produit à Paris. 
        Tim Cook, le PDG de l'entreprise, a déclaré que ce produit révolutionnera le marché. 
        La présentation a eu lieu le 15 septembre 2023 et a attiré plus de 1000 spectateurs.
        """
        display_result("7. Extraction d'entités", tools.extract_entities(text_for_entities))
        
        # 8. Vérification des faits (simulation)
        statement = "La Tour Eiffel mesure 330 mètres de hauteur."
        display_result(f"8. Vérification de '{statement}'", tools.fact_check(statement))
        
        # 9. Utilisation du cache
        print("\n9. Test du cache:")
        
        # Première requête (non mise en cache)
        start_time = time.time()
        result1 = tools.web_search("Polyad AI framework", max_results=2)
        time1 = time.time() - start_time
        print(f"  Première requête: {time1:.3f}s")
        
        # Deuxième requête (devrait utiliser le cache)
        start_time = time.time()
        result2 = tools.web_search("Polyad AI framework", max_results=2)
        time2 = time.time() - start_time
        print(f"  Deuxième requête: {time2:.3f}s")
        print(f"  Accélération: {time1/time2 if time2 > 0 else 'infinie'}x")
        
        # 10. Statistiques des outils
        display_result("10. Statistiques des outils", tools.get_stats())
        
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        # Nettoyer les ressources
        try:
            tools.cleanup()
            print("\nNettoyage des ressources terminé.")
        except Exception as e:
            print(f"Erreur lors du nettoyage: {e}")
    
    print("\nDémonstration terminée.")

if __name__ == "__main__":
    main()
