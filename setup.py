from setuptools import setup, find_packages

setup(
    name="polyad",
    version="0.1.0",
    description="Polyad AI - Agent autonome polyvalent",
    author="Mehdi Whb",
    author_email="contact@polyad.ai",
    url="https://github.com/mehdiwhb/polyad",
    packages=find_packages(),
    install_requires=[
        "transformers==4.49.0",
        "torch==2.2.2+cu118",
        "numpy==2.2.4",
        "ollama==0.4.7",
        "faiss-gpu>=1.7.4",
        "bitsandbytes>=0.42.0",
        "accelerate==0.26.0",
        "opencv-python==4.9.0.80",
        "pyautogui==0.9.54",
        "sounddevice==0.4.6",
        "soundfile==0.12.1",
        "aiohttp==3.11.14",
        "requests==2.32.3",
        "cachetools==5.4.0",
        "prometheus-client==0.20.0",
        "grafana-api>=1.0.3",
        "redis==5.0.1",
        "pytest==7.4.4",
        "black>=24.10.0",
        "mypy==1.8.0",
        "psutil==5.9.8",
        "python-dotenv==1.0.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X"
    ],
    python_requires=">=3.11",
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
