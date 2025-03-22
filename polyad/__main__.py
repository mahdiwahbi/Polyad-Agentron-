import os
import logging
import asyncio
from dotenv import load_dotenv
from polyad.utils.config import ConfigManager
from polyad.utils.logging import setup_logging
from polyad.core.agent import PolyadAgent

# Charger les variables d'environnement
load_dotenv()

# Configurer le logging
setup_logging()

# Charger la configuration
config = ConfigManager()

def main():
    try:
        # Initialiser l'agent
        agent = PolyadAgent(config=config)

        # Démarrer l'agent
        logging.info("Démarrage de l'agent Polyad...")
        asyncio.run(agent.start())

        # Boucle principale
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logging.info("Arrêt demandé par l'utilisateur...")

        # Arrêter proprement l'agent
        logging.info("Arrêt de l'agent en cours...")
        asyncio.run(agent.stop())

    except Exception as e:
        logging.error(f"Erreur critique : {str(e)}")
        raise

if __name__ == "__main__":
    main()
