#!/usr/bin/env python3
import os
import sys
import time
from polyad import Polyad
from utils.logger import logger
from utils.monitoring import monitor

def test_polyad():
    """Test rapide des fonctionnalités principales de Polyad"""
    logger.info("Démarrage du test rapide de Polyad")
    
    try:
        # 1. Initialisation de Polyad
        polyad = Polyad()
        logger.info(" Polyad initialisé avec succès")
        
        # 2. Test du monitoring système
        metrics = monitor.collect_metrics()
        logger.info(" Monitoring système fonctionnel", extra={"metrics": metrics})
        
        # 3. Test de l'inférence simple
        test_task = "Quelle est la capitale de la France?"
        logger.info(f"Test d'inférence avec la tâche: {test_task}")
        
        result = polyad.parallel_inference(test_task)
        logger.info(" Inférence réussie", extra={"result": result})
        
        # 4. Test des outils asynchrones
        async_result = polyad.loop.run_until_complete(
            polyad.async_tools.run_async(
                lambda: "Test async réussi",
                timeout=5.0
            )
        )
        logger.info(" Outils asynchrones fonctionnels", extra={"result": async_result})
        
        # 5. Vérification des statistiques
        stats = polyad.stats
        logger.info(" Statistiques disponibles", extra={"stats": stats})
        
        # 6. Test de la gestion des ressources
        health = monitor.get_system_health()
        logger.info(" Santé système vérifiée", extra={"health": health})
        
        return True, "Tous les tests ont réussi"
        
    except Exception as e:
        logger.error(f" Erreur pendant les tests: {str(e)}")
        return False, str(e)

def main():
    """Point d'entrée principal"""
    print(" Démarrage des tests Polyad...")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists("polyad.py"):
        print(" Erreur: Exécutez ce script depuis le répertoire racine de Polyad")
        sys.exit(1)
    
    # Exécuter les tests
    start_time = time.time()
    success, message = test_polyad()
    duration = time.time() - start_time
    
    # Afficher les résultats
    if success:
        print(f"""
 Tests terminés avec succès en {duration:.2f} secondes
 Message: {message}
 Consultez les logs pour plus de détails
        """)
        sys.exit(0)
    else:
        print(f"""
 Échec des tests après {duration:.2f} secondes
 Erreur: {message}
 Consultez les logs pour plus de détails
        """)
        sys.exit(1)

if __name__ == "__main__":
    main()