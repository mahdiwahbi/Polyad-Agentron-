from setuptools import setup, find_packages

setup(
    name="polyad",
    version="0.1.0",
    description="Polyad Agentron - Agent autonome pour la gestion de tâches",
    author="Mahdi Wahbi",
    author_email="mahdi.wahbi@polyad.com",
    url="https://github.com/mehdiwhb/polyad",
    packages=find_packages(),
    install_requires=[
        "transformers>=4.49.0",
        "torch>=2.2.2",
        "numpy>=1.26.3",
        "langchain>=0.1.0",
        "ollama>=0.1.0",
        "faiss-cpu>=1.7.4",
        "bitsandbytes>=0.42.0",
        "accelerate>=0.26.0",
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "websockets>=11.0.3",
        "python-telegram-bot>=20.7",
        "slack-sdk>=3.21.0",
        "psutil>=5.9.0",
        "prometheus-client>=0.20.0",
        "grafana-api>=1.0.3",
        "redis>=4.5.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "black>=23.11.0",
        "isort>=5.12.0",
        "mypy>=1.6.1",
        "flake8>=6.1.0",
        "PyQt6>=6.6.0",
        "PyQt6-WebEngine>=6.6.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "structlog>=23.2.0",
        "cryptography>=41.0.0",
        "easyocr>=1.7.1",
        "sounddevice>=0.4.6",
        "soundfile>=0.12.1"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    entry_points={
        "console_scripts": [
            "polyad=polyad.__main__:main"
        ]
    },
    package_data={
        "polyad": ["*.json", "*.yaml", "*.env.example"]
    },
    include_package_data=True
)
