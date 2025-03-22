#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
from typing import List, Dict, Any, Tuple
from utils.logger import logger
from utils.monitoring import monitor

class TestRunner:
    def __init__(self):
        """Initialise le runner de tests"""
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
    def run_test(self, test_name: str, command: List[str]) -> Tuple[bool, str]:
        """
        Exécute un test spécifique
        
        Args:
            test_name: Nom du test
            command: Commande à exécuter
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        logger.info(f"Démarrage du test: {test_name}")
        start_time = time.time()
        
        try:
            # Exécuter la commande
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Enregistrer le résultat
            self.test_results.append({
                "name": test_name,
                "success": success,
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr
            })
            
            if success:
                logger.info(f"✅ Test réussi: {test_name} ({duration:.2f}s)")
                return True, "Test réussi"
            else:
                logger.error(f"❌ Test échoué: {test_name} ({duration:.2f}s)")
                return False, result.stderr
                
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            
            # Enregistrer l'échec
            self.test_results.append({
                "name": test_name,
                "success": False,
                "duration": duration,
                "output": e.stdout,
                "error": e.stderr
            })
            
            logger.error(f"❌ Test échoué: {test_name} ({duration:.2f}s)")
            return False, str(e)
            
    def run_all_tests(self) -> bool:
        """
        Exécute tous les tests disponibles
        
        Returns:
            bool: True si tous les tests ont réussi
        """
        tests = [
            ("Test Rapide", ["python3", "quick_test.py"]),
            ("Test Ressources", ["python3", "test_polyad.py", "--component", "resource"]),
            ("Test Outils", ["python3", "test_polyad.py", "--component", "tools"]),
            ("Test Async", ["python3", "test_polyad.py", "--component", "async"]),
            ("Test Polyad", ["python3", "test_polyad.py", "--component", "polyad"])
        ]
        
        all_success = True
        for test_name, command in tests:
            success, _ = self.run_test(test_name, command)
            if not success:
                all_success = False
                
        return all_success
        
    def print_summary(self):
        """Affiche un résumé des tests"""
        total_duration = time.time() - self.start_time
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test["success"])
        
        print("\n" + "="*50)
        print("📊 RÉSUMÉ DES TESTS")
        print("="*50)
        print(f"Durée totale: {total_duration:.2f} secondes")
        print(f"Tests réussis: {successful_tests}/{total_tests}")
        print("-"*50)
        
        # Afficher les résultats individuels
        for test in self.test_results:
            status = "✅" if test["success"] else "❌"
            print(f"{status} {test['name']}: {test['duration']:.2f}s")
            if not test["success"]:
                print(f"   Erreur: {test['error']}")
        
        print("="*50)
        
def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Exécute tous les tests Polyad")
    parser.add_argument("--monitor", action="store_true", 
                       help="Active le monitoring système pendant les tests")
    args = parser.parse_args()
    
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists("polyad.py"):
        print("❌ Erreur: Exécutez ce script depuis le répertoire racine de Polyad")
        sys.exit(1)
    
    # Démarrer le monitoring si demandé
    if args.monitor:
        logger.info("Démarrage du monitoring système")
        monitor.collect_metrics()
    
    # Exécuter les tests
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Afficher le résumé
    runner.print_summary()
    
    # Sauvegarder les métriques si le monitoring était actif
    if args.monitor:
        monitor.save_metrics()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()