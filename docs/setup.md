# Setup Guide

## Prerequisites
- macOS Ventura or later
- Xcode Command Line Tools
- Python 3.11+

## Installation Steps

1. **System Dependencies**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install ollama python@3.11 portaudio ffmpeg
```

2. **Python Dependencies**
```bash
pip3 install -r requirements.txt
```

3. **Models Setup**
```bash
ollama pull gemma3:12b-q4_0
ollama pull gemma3:12b-q2_K
```

4. **Configuration**
Edit config.py to match your system:
```python
SYSTEM_LIMITS = {
    "max_cpu_percent": 80,
    "max_temp": 80,
    "min_free_ram": 1.0
}
```

## Verification
Run the test script:
```python
python3 -c "from polyad import Polyad; agent = Polyad(); print(agent.run('test'))"
```

## Troubleshooting
1. Memory Issues
   - Ensure swap is disabled
   - Check available RAM
2. GPU Issues
   - Verify Metal support
   - Check temperature sensors
3. Model Issues
   - Verify Ollama installation
   - Check model downloads
