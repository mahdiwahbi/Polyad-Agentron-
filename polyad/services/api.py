from typing import Dict, Any, Optional, List
import aiohttp
import json
from polyad.utils.config import ConfigManager
from polyad.utils.logging import get_logger

class APIManager:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = get_logger(__name__)
        self.session = None
        self.api_keys = self._load_api_keys()
        self.base_urls = self._load_base_urls()

    async def initialize(self):
        """Initialize the aiohttp session"""
        self.session = aiohttp.ClientSession()

    async def shutdown(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from configuration"""
        api_keys = {}
        for service, key in self.config.get('api_keys', {}).items():
            api_keys[service] = key
        return api_keys

    def _load_base_urls(self) -> Dict[str, str]:
        """Load base URLs from configuration"""
        base_urls = {}
        for service, url in self.config.get('api_base_urls', {}).items():
            base_urls[service] = url
        return base_urls

    async def make_request(
        self,
        service: str,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make an API request"""
        if not self.session:
            raise RuntimeError("APIManager not initialized")

        url = self.base_urls.get(service)
        if not url:
            raise ValueError(f"No base URL configured for service: {service}")

        full_url = f"{url}{endpoint}"
        
        if not headers:
            headers = {}
        
        # Add API key if available
        if service in self.api_keys:
            headers['Authorization'] = f'Bearer {self.api_keys[service]}'

        try:
            async with self.session.request(
                method,
                full_url,
                params=params,
                json=data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_msg}")
                
                return await response.json()
        except Exception as e:
            self.logger.error(f"Error making API request to {service}: {str(e)}")
            raise

    async def get_weather(self, location: str) -> Dict:
        """Get weather information for a location"""
        try:
            response = await self.make_request(
                'weather',
                f'/weather?q={location}'
            )
            return {
                'temperature': response['main']['temp'],
                'description': response['weather'][0]['description'],
                'humidity': response['main']['humidity']
            }
        except Exception as e:
            self.logger.error(f"Error getting weather: {str(e)}")
            raise

    async def get_news(self, category: str = 'general') -> Dict:
        """Get news articles"""
        try:
            response = await self.make_request(
                'news',
                f'/top-headlines?category={category}'
            )
            return {
                'articles': response['articles'][:5]  # Return top 5 articles
            }
        except Exception as e:
            self.logger.error(f"Error getting news: {str(e)}")
            raise

    async def get_stock_price(self, symbol: str) -> Dict:
        """Get stock price information"""
        try:
            response = await self.make_request(
                'stock',
                f'/quote?symbol={symbol}'
            )
            return {
                'price': response['price'],
                'change': response['change'],
                'volume': response['volume']
            }
        except Exception as e:
            self.logger.error(f"Error getting stock price: {str(e)}")
            raise

    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to a different language"""
        try:
            response = await self.make_request(
                'translate',
                '/translate',
                method='POST',
                data={
                    'text': text,
                    'target_language': target_language
                }
            )
            return response['translated_text']
        except Exception as e:
            self.logger.error(f"Error translating text: {str(e)}")
            raise
