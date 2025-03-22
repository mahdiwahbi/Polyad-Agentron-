#!/usr/bin/env python3
import asyncio
import sys
from core.autonomous_agent import AutonomousAgent
from utils.logger import logger

async def demo():
    """Démonstration des capacités de l'agent"""
    try:
        print("\nInitialisation de l'agent Polyad...")
        agent = AutonomousAgent()
        
        if not await agent.initialize():
            print("Échec de l'initialisation")
            return 1
            
        print("\nAgent initialisé avec succès!")
        print("\nCapacités disponibles:")
        print(f"- Vision: {agent.capabilities['vision']}")
        print(f"- Audio: {agent.capabilities['audio']}")
        print(f"- Action: {agent.capabilities['action']}")
        
        while True:
            print("\nOptions disponibles:")
            print("1. Test Vision")
            print("2. Test Audio")
            print("3. Test Action")
            print("4. Voir les capacités")
            print("5. Quitter")
            
            choice = input("\nChoisissez une option (1-5): ")
            
            if choice == "1":
                print("\nTest de vision...")
                result = await agent.process_visual()
                print(f"Résultat: {result}")
                
            elif choice == "2":
                print("\nTest audio (enregistrement de 5 secondes)...")
                result = await agent.process_audio()
                print(f"Résultat: {result}")
                
            elif choice == "3":
                print("\nTest d'action (clic à (100, 100))...")
                action = {'type': 'click', 'coordinates': (100, 100)}
                result = await agent.execute_action(action)
                print(f"Résultat: {result}")
                
            elif choice == "4":
                print("\nCapacités actuelles:")
                caps = agent.capabilities
                print("\nMéta-apprentissage:")
                print(f"- Stratégies: {caps['meta_learning']['strategies']}")
                print(f"- Performance: {caps['meta_learning']['performance']}")
                print("\nFew-shot learning:")
                print(f"- Exemples: {caps['few_shot']['examples']}")
                print(f"- Taux de succès: {caps['few_shot']['success_rate']}")
                print("\nContextuel:")
                print(f"- Contextes: {caps['contextual']['contexts']}")
                print(f"- Adaptations: {caps['contextual']['adaptations']}")
                print("\nMémoire:")
                print(f"- Taille du vector store: {caps['memory']['vector_store_size']}")
                
            elif choice == "5":
                print("\nSauvegarde de l'état...")
                await agent.save_state()
                print("Au revoir!")
                break
                
            else:
                print("\nOption invalide")
                
    except KeyboardInterrupt:
        print("\nInterruption détectée")
        await agent.save_state()
        print("État sauvegardé")
        
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return 1
        
if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nFermeture forcée")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)
