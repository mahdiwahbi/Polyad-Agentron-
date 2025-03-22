from langchain.tools import DuckDuckGoSearchRun
import subprocess
import cv2
import speech_recognition as sr
import sqlite3
import hashlib
import json
import os
import time
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Union
from PIL import Image
import requests
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'tools.log')),
        logging.StreamHandler()
    ]
)

class PolyadTools:
    def __init__(self, cache_ttl: int = 86400):
        """
        Initialise les outils Polyad avec gestion de cache avancée
        
        Args:
            cache_ttl: Durée de vie du cache en secondes (par défaut: 24h)
        """
        # Initialiser les outils de recherche
        self.search = DuckDuckGoSearchRun()
        
        # Initialiser la reconnaissance vocale
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Ajuster selon l'environnement
        
        # Configuration du cache
        self.cache_ttl = cache_ttl
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialiser la base de données de cache
        self.setup_cache()
        
        # Statistiques d'utilisation
        self.stats = {
            "web_searches": 0,
            "image_processes": 0,
            "system_commands": 0,
            "voice_recognitions": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logging.info("Outils Polyad initialisés avec succès")
        
    def setup_cache(self):
        """Initialise la base de données de cache SQLite avec métadonnées"""
        try:
            cache_path = os.path.join(self.cache_dir, 'polyad_cache.db')
            self.conn = sqlite3.connect(cache_path)
            
            # Créer la table de cache avec métadonnées
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME,
                    access_count INTEGER DEFAULT 1,
                    last_access DATETIME,
                    metadata TEXT
                )
            ''')
            
            # Créer un index sur timestamp pour les opérations de nettoyage
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
            
            # Nettoyer le cache au démarrage
            self.cleanup_cache()
            
            logging.info(f"Cache initialisé: {cache_path}")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation du cache: {e}")
        
    def get_cached(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé de cache
            
        Returns:
            Any: Valeur du cache ou None si non trouvée
        """
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            # Vérifier si la clé existe et n'est pas expirée
            result = self.conn.execute('''
                SELECT value, timestamp FROM cache 
                WHERE key = ?
            ''', (key_hash,)).fetchone()
            
            if not result:
                self.stats["cache_misses"] += 1
                return None
                
            value, timestamp = result
            
            # Vérifier si l'entrée est expirée
            cache_time = datetime.fromisoformat(timestamp)
            if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
                logging.debug(f"Cache expiré pour {key_hash[:8]}")
                self.stats["cache_misses"] += 1
                return None
                
            # Mettre à jour les statistiques d'accès
            self.conn.execute('''
                UPDATE cache SET 
                access_count = access_count + 1,
                last_access = datetime()
                WHERE key = ?
            ''', (key_hash,))
            self.conn.commit()
            
            self.stats["cache_hits"] += 1
            return json.loads(value)
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération du cache: {e}")
            return None
        
    def cache_result(self, key: str, value: Any, metadata: Dict[str, Any] = None):
        """
        Stocke une valeur dans le cache
        
        Args:
            key: Clé de cache
            value: Valeur à stocker
            metadata: Métadonnées associées à l'entrée
        """
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            # Convertir les valeurs en JSON
            value_json = json.dumps(value)
            metadata_json = json.dumps(metadata or {})
            
            # Stocker dans le cache
            self.conn.execute('''
                INSERT OR REPLACE INTO cache 
                (key, value, timestamp, last_access, metadata) 
                VALUES (?, ?, datetime(), datetime(), ?)
            ''', (key_hash, value_json, metadata_json))
            
            self.conn.commit()
            logging.debug(f"Valeur mise en cache: {key_hash[:8]}")
            
        except Exception as e:
            logging.error(f"Erreur lors du stockage dans le cache: {e}")
        
    def web_search(self, query: str) -> str:
        """
        Effectue une recherche web avec mise en cache
        
        Args:
            query: Requête de recherche
            
        Returns:
            str: Résultats de la recherche
        """
        # Vérifier le cache
        cache_key = f"web_search_{query}"
        cached = self.get_cached(cache_key)
        if cached:
            logging.info(f"Résultat de recherche trouvé en cache pour: {query}")
            return cached
            
        # Effectuer la recherche
        try:
            self.stats["web_searches"] += 1
            result = self.search.run(query)
            
            # Mettre en cache
            self.cache_result(
                cache_key, 
                result,
                {"type": "web_search", "query": query}
            )
            
            return result
        except Exception as e:
            logging.error(f"Erreur lors de la recherche web: {e}")
            return f"Erreur de recherche: {str(e)}"
        
    def run_system_command(self, command: str, timeout: int = 30) -> str:
        """
        Exécute une commande système avec sécurité renforcée
        
        Args:
            command: Commande à exécuter
            timeout: Délai d'expiration en secondes
            
        Returns:
            str: Résultat de la commande
        """
        # Vérifier si la commande est autorisée
        if any(unsafe in command.lower() for unsafe in ["rm -rf", "sudo rm", "mkfs"]):
            logging.warning(f"Commande potentiellement dangereuse bloquée: {command}")
            return "Erreur: Commande potentiellement dangereuse non autorisée"
        
        try:
            self.stats["system_commands"] += 1
            logging.info(f"Exécution de la commande: {command}")
            
            # Exécuter la commande de manière sécurisée
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                check=False,  # Ne pas lever d'exception en cas d'erreur
                shell=False,  # Pas d'injection shell
                timeout=timeout  # Délai d'expiration
            )
            
            # Gérer les erreurs
            if result.returncode != 0:
                logging.warning(f"Commande terminée avec code {result.returncode}: {result.stderr}")
                return f"Erreur (code {result.returncode}): {result.stderr}"
                
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logging.error(f"Délai d'expiration pour la commande: {command}")
            return f"Erreur: Délai d'expiration après {timeout}s"
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la commande: {e}")
            return f"Erreur: {str(e)}"
            
    def process_image(self, image_path: str, target_size: tuple = (512, 512)) -> Union[np.ndarray, str]:
        """
        Traite une image avec mise en cache
        
        Args:
            image_path: Chemin vers l'image
            target_size: Taille cible (largeur, hauteur)
            
        Returns:
            np.ndarray ou str: Image traitée ou message d'erreur
        """
        # Vérifier le cache
        cache_key = f"img_{image_path}_{target_size[0]}x{target_size[1]}"
        cached = self.get_cached(cache_key)
        if cached:
            logging.info(f"Image trouvée en cache: {os.path.basename(image_path)}")
            return np.array(cached)
        
        try:
            self.stats["image_processes"] += 1
            
            # Charger l'image
            img = cv2.imread(image_path)
            if img is None:
                logging.error(f"Impossible de charger l'image: {image_path}")
                return "Erreur: Impossible de charger l'image"
                
            # Redimensionner
            processed = cv2.resize(img, target_size)
            
            # Mettre en cache (convertir en liste pour JSON)
            self.cache_result(
                cache_key, 
                processed.tolist(),
                {
                    "type": "image", 
                    "path": image_path,
                    "size": f"{target_size[0]}x{target_size[1]}"
                }
            )
            
            return processed
            
        except Exception as e:
            logging.error(f"Erreur lors du traitement de l'image: {e}")
            return f"Erreur: {str(e)}"
    
    def recognize_speech(self, duration: int = 5) -> str:
        """
        Reconnaît la parole à partir du microphone
        
        Args:
            duration: Durée d'enregistrement en secondes
            
        Returns:
            str: Texte reconnu ou message d'erreur
        """
        try:
            self.stats["voice_recognitions"] += 1
            
            # Utiliser le microphone comme source
            with sr.Microphone() as source:
                logging.info(f"Écoute pendant {duration} secondes...")
                
                # Ajuster pour le bruit ambiant
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Enregistrer l'audio
                audio = self.recognizer.listen(source, timeout=duration)
                
                # Reconnaître avec Google Speech Recognition
                text = self.recognizer.recognize_google(audio, language="fr-FR")
                logging.info(f"Texte reconnu: {text}")
                
                return text
                
        except sr.UnknownValueError:
            logging.warning("La parole n'a pas pu être reconnue")
            return "Erreur: Parole non reconnue"
        except sr.RequestError as e:
            logging.error(f"Erreur de service de reconnaissance: {e}")
            return f"Erreur de service: {str(e)}"
        except Exception as e:
            logging.error(f"Erreur lors de la reconnaissance vocale: {e}")
            return f"Erreur: {str(e)}"
    
    def download_image(self, url: str, save_path: Optional[str] = None) -> str:
        """
        Télécharge une image depuis une URL
        
        Args:
            url: URL de l'image
            save_path: Chemin où sauvegarder l'image (optionnel)
            
        Returns:
            str: Chemin de l'image sauvegardée ou message d'erreur
        """
        try:
            # Générer un nom de fichier si non fourni
            if not save_path:
                filename = f"image_{int(time.time())}.jpg"
                save_path = os.path.join(self.cache_dir, filename)
                
            # Télécharger l'image
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Vérifier que c'est bien une image
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return f"Erreur: Le contenu n'est pas une image ({content_type})"
                
            # Sauvegarder l'image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Image téléchargée: {save_path}")
            return save_path
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur lors du téléchargement de l'image: {e}")
            return f"Erreur: {str(e)}"
            
    def cleanup_cache(self, max_size_mb: int = 500):
        """
        Nettoie les entrées de cache anciennes ou peu utilisées
        
        Args:
            max_size_mb: Taille maximale du cache en Mo
        """
        try:
            # Supprimer les entrées expirées
            self.conn.execute('''
                DELETE FROM cache 
                WHERE datetime('now') > datetime(timestamp, '+' || ? || ' seconds')
            ''', (str(self.cache_ttl),))
            
            # Obtenir la taille actuelle du cache
            db_path = self.conn.execute("PRAGMA database_list").fetchone()[2]
            db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            
            # Si le cache est trop grand, supprimer les entrées les moins utilisées
            if db_size_mb > max_size_mb:
                logging.info(f"Nettoyage du cache (taille: {db_size_mb:.2f} Mo)")
                
                # Supprimer les entrées les moins accédées
                self.conn.execute('''
                    DELETE FROM cache 
                    WHERE key IN (
                        SELECT key FROM cache 
                        ORDER BY access_count ASC, last_access ASC 
                        LIMIT (SELECT count(*) / 4 FROM cache)
                    )
                ''')
            
            # Compacter la base de données
            self.conn.execute("VACUUM")
            self.conn.commit()
            
            # Nettoyer les fichiers d'images dans le dossier cache
            self._cleanup_image_files()
            
            logging.info("Nettoyage du cache terminé")
            
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage du cache: {e}")
    
    def _cleanup_image_files(self):
        """Nettoie les fichiers d'images anciens dans le dossier cache"""
        try:
            # Obtenir tous les fichiers d'images
            image_files = [f for f in os.listdir(self.cache_dir) 
                          if f.endswith(('.jpg', '.png', '.jpeg')) and 
                          os.path.isfile(os.path.join(self.cache_dir, f))]
            
            # Trier par date de modification
            image_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.cache_dir, f)))
            
            # Garder seulement les 100 plus récents
            if len(image_files) > 100:
                for f in image_files[:-100]:
                    try:
                        os.remove(os.path.join(self.cache_dir, f))
                    except:
                        pass
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage des fichiers d'images: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'utilisation des outils
        
        Returns:
            dict: Statistiques d'utilisation
        """
        # Calculer le ratio de hit du cache
        total_cache_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_ratio = self.stats["cache_hits"] / total_cache_requests if total_cache_requests > 0 else 0
        
        return {
            **self.stats,
            "cache_hit_ratio": cache_hit_ratio
        }
        
    def cleanup(self):
        """
        Nettoie les ressources et ferme les connexions
        """
        try:
            # Nettoyer le cache
            self.cleanup_cache()
            
            # Fermer la connexion à la base de données
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                logging.info("Connexion à la base de données du cache fermée")
                
            # Libérer d'autres ressources si nécessaire
            logging.info("Nettoyage des ressources PolyadTools terminé")
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage des ressources: {e}")
    
    def __del__(self):
        """Nettoyage lors de la destruction"""
        try:
            self.cleanup_cache()
            self.conn.close()
            logging.info("Connexion à la base de données du cache fermée")
        except:
            pass
