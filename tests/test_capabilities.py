import pytest
import asyncio
from polyad.core.learning_engine import LearningEngine
from polyad.config import load_config
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
async def learning_engine(test_config):
    """Learning Engine fixture for testing"""
    engine = LearningEngine(test_config)
    yield engine
    await engine.shutdown()

@pytest.mark.asyncio
async def test_natural_language_understanding(learning_engine):
    """Test natural language understanding capability"""
    logger.info("Testing Natural Language Understanding...")
    prompt = "What is the capital of France?"
    response = await learning_engine.process_message(prompt)
    assert "Paris" in response, "Failed to understand basic question"
    logger.info("Natural Language Understanding: ")

@pytest.mark.asyncio
async def test_code_generation(learning_engine):
    """Test code generation capability"""
    logger.info("Testing Code Generation...")
    prompt = "Write a Python function to reverse a string"
    response = await learning_engine.process_message(prompt)
    assert "def reverse_string" in response and "return" in response, "Failed to generate code"
    logger.info("Code Generation: ")

@pytest.mark.asyncio
async def test_problem_solving(learning_engine):
    """Test problem solving capability"""
    logger.info("Testing Problem Solving...")
    prompt = "Calculate the factorial of 5"
    response = await learning_engine.process_message(prompt)
    assert "120" in response, "Failed to solve mathematical problem"
    logger.info("Problem Solving: ")

@pytest.mark.asyncio
async def test_web_search(learning_engine):
    """Test web search capability"""
    logger.info("Testing Web Search...")
    prompt = "What is the current population of New York City?"
    response = await learning_engine.process_message(prompt)
    assert "million" in response, "Failed to perform web search"
    logger.info("Web Search: ")

@pytest.mark.asyncio
async def test_system_command_execution(learning_engine):
    """Test system command execution capability"""
    logger.info("Testing System Command Execution...")
    prompt = "List the contents of the current directory"
    response = await learning_engine.process_message(prompt)
    assert "tests" in response, "Failed to execute system command"
    logger.info("System Command Execution: ")

@pytest.mark.asyncio
async def test_api_integration(learning_engine):
    """Test API integration capability"""
    logger.info("Testing API Integration...")
    prompt = "What's the weather in Paris?"
    response = await learning_engine.process_message(prompt)
    assert "temperature" in response, "Failed to integrate with weather API"
    logger.info("API Integration: ")

@pytest.mark.asyncio
async def test_vision_processing(learning_engine):
    """Test vision processing capability"""
    logger.info("Testing Vision Processing...")
    prompt = "Describe this image: https://example.com/image.jpg"
    response = await learning_engine.process_message(prompt)
    assert "image" in response, "Failed to process vision request"
    logger.info("Vision Processing: ")

@pytest.mark.asyncio
async def test_audio_processing(learning_engine):
    """Test audio processing capability"""
    logger.info("Testing Audio Processing...")
    prompt = "Transcribe this audio: https://example.com/audio.mp3"
    response = await learning_engine.process_message(prompt)
    assert "transcription" in response, "Failed to process audio"
    logger.info("Audio Processing: ")

@pytest.mark.asyncio
async def test_gui_automation(learning_engine):
    """Test GUI automation capability"""
    logger.info("Testing GUI Automation...")
    prompt = "Open the browser and navigate to google.com"
    response = await learning_engine.process_message(prompt)
    assert "browser" in response, "Failed to perform GUI automation"
    logger.info("GUI Automation: ")

@pytest.mark.asyncio
async def test_data_analysis(learning_engine):
    """Test data analysis capability"""
    logger.info("Testing Data Analysis...")
    prompt = "Analyze this dataset: https://example.com/data.csv"
    response = await learning_engine.process_message(prompt)
    assert "analysis" in response, "Failed to perform data analysis"
    logger.info("Data Analysis: ")
