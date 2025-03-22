#!/usr/bin/env python3
import asyncio
import signal
import sys
from core.polyad import Polyad
from utils.logger import logger

async def main():
    """Main entry point for Polyad agent"""
    try:
        # Initialize Polyad agent
        agent = Polyad()
        if not await agent.initialize():
            logger.error("Failed to initialize Polyad")
            return 1

        # Register signal handlers
        def signal_handler(sig, frame):
            logger.info("Shutting down Polyad...")
            asyncio.create_task(cleanup(agent))
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Example task to demonstrate capabilities
        task = {
            'type': 'system',
            'action': 'monitor',
            'components': ['cpu', 'memory', 'gpu', 'network']
        }

        # Process task
        logger.info("Starting system monitoring...")
        result = await agent.process_task(task)

        if 'error' in result:
            logger.error(f"Task failed: {result['error']}")
            return 1

        logger.info("System monitoring active")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Polyad failed: {e}")
        return 1

async def cleanup(agent):
    """Cleanup resources"""
    try:
        # Save current state
        await agent.save_state()
        logger.info("State saved successfully")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Polyad stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
