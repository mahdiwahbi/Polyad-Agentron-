import pytest
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polyad.services.api import APIManager
from polyad.services.search import SearchService
from polyad.services.security import SecurityManager
from polyad.utils.error_handling import ErrorHandler
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
async def api_manager():
    """API Manager fixture for testing"""
    manager = APIManager()
    await manager.initialize()
    yield manager
    await manager.shutdown()

@pytest.fixture(scope="module")
async def search_service():
    """Search Service fixture for testing"""
    service = SearchService()
    await service.initialize()
    yield service
    await service.shutdown()

@pytest.fixture(scope="module")
def security_manager():
    """Security Manager fixture for testing"""
    return SecurityManager()

@pytest.mark.asyncio
async def test_weather_api(api_manager):
    """Test weather API integration"""
    try:
        result = await api_manager.get_weather("Paris")
        assert 'temperature' in result
        logger.info("Weather API test: ")
    except Exception as e:
        logger.error(f"Weather API test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_news_api(api_manager):
    """Test news API integration"""
    try:
        result = await api_manager.get_news("technology")
        assert isinstance(result, dict)
        logger.info("News API test: ")
    except Exception as e:
        logger.error(f"News API test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_stock_api(api_manager):
    """Test stock price API integration"""
    try:
        result = await api_manager.get_stock_price("AAPL")
        assert 'price' in result
        logger.info("Stock API test: ")
    except Exception as e:
        logger.error(f"Stock API test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_web_search(search_service):
    """Test web search capability"""
    try:
        results = await search_service.search_web("Python programming")
        assert len(results) > 0
        logger.info("Web search test: ")
    except Exception as e:
        logger.error(f"Web search test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_image_search(search_service):
    """Test image search capability"""
    try:
        results = await search_service.search_images("sunset")
        assert len(results) > 0
        logger.info("Image search test: ")
    except Exception as e:
        logger.error(f"Image search test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_news_search(search_service):
    """Test news search capability"""
    try:
        results = await search_service.search_news("AI technology")
        assert len(results) > 0
        logger.info("News search test: ")
    except Exception as e:
        logger.error(f"News search test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling system"""
    error_handler = ErrorHandler()
    try:
        error_info = error_handler.handle_error(
            Exception("Test error"),
            {
                'error_type': 'system',
                'component': 'test',
                'operation': 'test_operation'
            }
        )
        assert isinstance(error_info, dict)
        logger.info("Error handling test: ")
    except Exception as e:
        logger.error(f"Error handling test failed: {str(e)}")
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_security_features(security_manager):
    """Test security features"""
    try:
        # Test encryption
        data = "test data"
        encrypted = security_manager.encrypt_data(data)
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == data

        # Test API key validation
        api_key = security_manager.generate_api_key()
        assert security_manager.validate_api_key(api_key, 'test')

        logger.info("Security features test: ")
    except Exception as e:
        logger.error(f"Security features test failed: {str(e)}")
        pytest.fail(str(e))
