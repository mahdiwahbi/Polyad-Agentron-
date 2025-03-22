from typing import Dict, Any, Optional, List
import aiohttp
from polyad.utils.config import ConfigManager
from polyad.utils.logging import get_logger
from polyad.utils.error_handling import ErrorHandler

class SearchService:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler()
        self.session = None
        self.search_engines = self._load_search_engines()

    async def initialize(self):
        """Initialize the aiohttp session"""
        self.session = aiohttp.ClientSession()

    async def shutdown(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

    def _load_search_engines(self) -> Dict[str, Dict]:
        """Load configured search engines"""
        engines = {}
        for engine, config in self.config.get('search_engines', {}).items():
            engines[engine] = config
        return engines

    async def search_web(self, query: str, engine: str = 'default') -> List[Dict]:
        """Perform a web search using the specified engine"""
        if not self.session:
            raise RuntimeError("SearchService not initialized")

        engine_config = self.search_engines.get(engine)
        if not engine_config:
            engine_config = self.search_engines.get('default')
            if not engine_config:
                raise ValueError("No search engine configured")

        try:
            params = {
                'q': query,
                'limit': engine_config.get('results_limit', 10)
            }

            async with self.session.get(
                engine_config['base_url'],
                params=params,
                headers=engine_config.get('headers', {})
            ) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    raise Exception(f"Search request failed: {response.status} - {error_msg}")

                result = await response.json()
                return result.get('items', [])

        except Exception as e:
            error_info = self.error_handler.handle_error(
                e,
                {
                    'error_type': 'search',
                    'component': 'web_search',
                    'operation': 'search_web'
                }
            )
            self.logger.error(f"Web search failed: {error_info}")
            raise

    async def search_images(self, query: str, engine: str = 'default') -> List[Dict]:
        """Perform an image search using the specified engine"""
        if not self.session:
            raise RuntimeError("SearchService not initialized")

        engine_config = self.search_engines.get(engine)
        if not engine_config:
            engine_config = self.search_engines.get('default')
            if not engine_config:
                raise ValueError("No search engine configured")

        try:
            params = {
                'q': query,
                'type': 'image',
                'limit': engine_config.get('results_limit', 10)
            }

            async with self.session.get(
                engine_config['base_url'],
                params=params,
                headers=engine_config.get('headers', {})
            ) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    raise Exception(f"Image search failed: {response.status} - {error_msg}")

                result = await response.json()
                return result.get('items', [])

        except Exception as e:
            error_info = self.error_handler.handle_error(
                e,
                {
                    'error_type': 'search',
                    'component': 'image_search',
                    'operation': 'search_images'
                }
            )
            self.logger.error(f"Image search failed: {error_info}")
            raise

    async def search_news(self, query: str, engine: str = 'default') -> List[Dict]:
        """Perform a news search using the specified engine"""
        if not self.session:
            raise RuntimeError("SearchService not initialized")

        engine_config = self.search_engines.get(engine)
        if not engine_config:
            engine_config = self.search_engines.get('default')
            if not engine_config:
                raise ValueError("No search engine configured")

        try:
            params = {
                'q': query,
                'type': 'news',
                'limit': engine_config.get('results_limit', 10)
            }

            async with self.session.get(
                engine_config['base_url'],
                params=params,
                headers=engine_config.get('headers', {})
            ) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    raise Exception(f"News search failed: {response.status} - {error_msg}")

                result = await response.json()
                return result.get('items', [])

        except Exception as e:
            error_info = self.error_handler.handle_error(
                e,
                {
                    'error_type': 'search',
                    'component': 'news_search',
                    'operation': 'search_news'
                }
            )
            self.logger.error(f"News search failed: {error_info}")
            raise
