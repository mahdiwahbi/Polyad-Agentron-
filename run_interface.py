#!/usr/bin/env python3
import asyncio
import sys
from interface.cli import PolyadCLI
from utils.logger import logger

async def main():
    """Démarrer l'interface Polyad"""
    try:
        print("\nDémarrage de l'interface Polyad...")
        
        # Initialiser l'interface
        cli = PolyadCLI()
        if not await cli.initialize():
            logger.error("Échec de l'initialisation")
            return 1
            
        # Démarrer la boucle d'interface
        while True:
            try:
                command = input(cli.prompt).strip()
                if command.lower() == 'quit':
                    break
                    
                # Exécuter la commande
                await cli.onecmd(command)
                
            except KeyboardInterrupt:
                print("\nUtilisez 'quit' pour quitter proprement")
                continue
                
            except Exception as e:
                logger.error(f"Erreur de commande: {e}")
                
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        return 1
        
    finally:
        # Nettoyage
        await cli._cleanup()
        print("\nInterface Polyad fermée.")
        
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nFermeture forcée de l'interface")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)
