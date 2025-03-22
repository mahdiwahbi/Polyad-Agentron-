### Improved Prompt for Code Completion Agent

```
I need you to create a comprehensive and advanced platform called "Polyad: The Genie Agent," a fully autonomous and evolving general-purpose AI agent designed to run on a MacBook 2019 (Intel i7 6-core, 16 GB LPDDR3 RAM, dual GPU: Intel UHD 630 + AMD Radeon Pro 555X/560X with 4 GB GDDR5) under macOS Ventura. Polyad must act as a "genie" that fulfills a wide range of user wishes, autonomously learning to navigate the web, register for API services and other platforms, create accounts, and manage complex tasks in a human-like manner. Below are the detailed specifications and step-by-step guidance for building this platform.

### Technical Specifications
- **AI Model**: Use "gemma3:12b-it-q4_K_M" via Ollama (quantized, ~8-10 GB RAM footprint).
- **Learning Techniques**:
  - **Reinforcement Learning (RL)**: Implement a simple RL system to optimize actions through trial and error. Define a reward system (e.g., +1 for successful task completion, -1 for failure) to improve navigation and registration processes.
  - **LSTM for Contextual Memory**: Simulate LSTM-like behavior using `ConversationBufferMemory` with a 1000-token limit to maintain long-term context across interactions.
  - **Optimized Autoregressive Generation**: Enhance generation speed with pruning (skip unnecessary token predictions) and caching (store frequent responses in SQLite).
- **Framework**: Use LangChain as the core orchestration layer, integrating RL, memory, and a suite of tools.
- **Resource Management**:
  - **Dynamic Quantization**: Switch between q4_K_M (~8-10 GB) and q2_K (~6-8 GB) based on available RAM, monitored via `psutil`.
  - **System Monitoring**: Track CPU usage (limit at 25%), RAM (ensure >4GB free), and temperature (limit at 80°C using `smc` command), pausing execution with `time.sleep(60)` if thresholds are exceeded.
  - **Cloud Offloading**: Delegate heavy tasks to AWS Lambda or Heroku when local RAM drops below 4GB.
- **Target Environment**: Ensure compatibility with macOS Ventura, leveraging Metal for GPU acceleration where possible.

### Safety Limits
1. **CPU**:
   - Maximum usage: 25%
   - Warning threshold: 20%
   - Critical threshold: 15%

2. **Memory**:
   - Minimum available: 4GB
   - Warning threshold: 3GB
   - Critical threshold: 2GB

3. **GPU**:
   - Maximum usage: 25%
   - Warning threshold: 20%
   - Critical threshold: 15%

4. **Disk**:
   - Maximum usage: 75%
   - Warning threshold: 70%
   - Critical threshold: 85%

5. **Temperature**:
   - Maximum: 80°C
   - Warning threshold: 75°C
   - Critical threshold: 85°C

### Monitoring Intervals
- CPU: 5 seconds
- Memory: 10 seconds
- GPU: 10 seconds
- Disk: 30 seconds
- Temperature: 30 seconds

### Notification Configuration
- Channels: ['email', 'slack']
- Maximum alerts per hour:
  - Warning: 2/h
  - Critical: 4/h
- Retry attempts: 3
- Retry delay: 60 seconds

### Core Features and Functionalities
Polyad must include the following capabilities, each with specific implementation details:

1. **Autonomous Web Navigation and Registration**:
   - Use vision (Tesseract OCR and EasyOCR) to read web interfaces, identifying buttons (e.g., "Sign Up"), fields (e.g., "Email"), and instructions.
   - Navigate with Selenium and Playwright, performing clicks and text input via PyAutoGUI.
   - Register for services by generating temporary emails (Temp-Mail API), fake user data (Faker), and solving captchas (2Captcha for complex ones, RL for simple ones).
   - Example: "Register me on Canva" → Navigate to canva.com, locate "Sign Up," fill fields, and confirm via email.

2. **API Learning and Integration**:
   - Scrape API documentation using BeautifulSoup, read text with OCR if needed, and test endpoints with `requests`.
   - Store API keys securely in an encrypted file (OpenSSL).
   - Example: "Use Google Calendar to schedule an event" → Register, retrieve API key, and execute.

3. **Multimodal Interaction**:
   - **Vision**: Dynamically analyze screens, detect pop-ups, and adjust actions in real-time using OpenCV for image processing.
   - **Speech**: Listen to user commands (SpeechRecognition) and provide vocal feedback (gTTS), e.g., "Account created successfully."
   - Example: "Sign me up for Spotify vocally" → Listen to command, navigate, and confirm aloud.

4. **Proactive Behavior**:
   - Analyze past interactions (via LSTM memory) to suggest actions, e.g., "You write often; shall I set up Grammarly?"
   - Use external data (e.g., OpenWeatherMap for weather) to predict needs, e.g., "Rain tomorrow, book a taxi?"
   - Example: "Manage my day" → Schedule tasks, anticipate transport needs.

5. **Creative Content Generation**:
   - Generate text (articles, scripts), visuals (Canva API), audio (gTTS), and prototypes (Figma API).
   - Example: "Create a cooking blog" → Register on Medium, write, and publish.

6. **Professional Automation**:
   - Connect services with Zapier, manage clients (HubSpot API), translate text (DeepL API).
   - Process data with Pandas and visualize with Matplotlib.
   - Example: "Track my sales" → Register on HubSpot, automate reports.

7. **Education and Personal Growth**:
   - Create adaptive learning plans (e.g., coding via GitHub API), simulate scenarios (e.g., interviews with RL feedback).
   - Example: "Teach me Python" → Register on Codecademy, guide with exercises.

8. **Physical World Interaction**:
   - Order items online (Amazon API), control smart devices (Home Assistant).
   - Example: "Buy a Python book" → Register on Amazon, place order.

9. **Entertainment**:
   - Recommend movies/music (Netflix/Spotify APIs), create interactive games.
   - Example: "Plan a movie night" → Register on Netflix, organize.

10. **Problem Solving**:
    - Troubleshoot issues by reading errors (OCR), provide financial advice (Alpha Vantage).
    - Example: "Fix my Wi-Fi" → Diagnose, suggest steps.

### Tools and Dependencies
Incorporate these tools into the platform:
- **Vision**: Tesseract OCR, EasyOCR, OpenCV (screen reading, image analysis).
- **Speech**: SpeechRecognition (listening), gTTS, Espeak (speaking).
- **Web**: Selenium, Playwright (navigation), BeautifulSoup (scraping).
- **Account Creation**: Temp-Mail API, Faker (fake data), 2Captcha (captcha solving).
- **API/Security**: Requests (API calls), OpenSSL, Keyring (encryption).
- **Creative Tools**: Canva API, Figma API, Magenta (content generation).
- **Automation**: Zapier, HubSpot API, DeepL API (workflow, CRM, translation).
- **Data**: Pandas, Matplotlib (analysis, visualization).
- **Learning**: Scikit-learn (RL), TensorFlow Lite (lightweight ML).
- **Installation Commands**:
  ```
  brew install ollama python@3.11 portaudio tesseract
  pip install langchain langchain-ollama duckduckgo-search psutil opencv-python speechrecognition pyautogui faiss-cpu pyaudio selenium beautifulsoup4 pytesseract requests faker gtts scikit-learn tensorflow easyocr playwright pandas matplotlib
  ollama pull gemma3:12b-it-q4_K_M
  playwright install
  ```

### Step-by-Step Coding Instructions
Follow these steps to build Polyad:

1. **Initialize the Core Structure**:
   - Create a Python script (`polyad.py`) with imports for all dependencies.
   - Set up the Ollama model (`gemma3:12b-it-q4_K_M`), LangChain agent, and memory.
   - Example:
     ```python
     from langchain_ollama import OllamaLLM
     from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
     from langchain.memory import ConversationBufferMemory
     llm = OllamaLLM(model="gemma3:12b-it-q4_K_M")
     memory = ConversationBufferMemory(max_token_limit=1000)
     ```

2. **Implement Resource Management**:
   - Define a function `check_resources()` to monitor CPU, RAM, and temperature, pausing if overloaded.
   - Example:
     ```python
     import psutil, subprocess, time
     def check_resources():
         cpu = psutil.cpu_percent()
         ram = psutil.virtual_memory().available / (1024 ** 3)
         temp = subprocess.run("smc -k TC0P -r", shell=True, capture_output=True).stdout
         temp_value = float(temp.split()[2]) if temp else 80
         if cpu > 25 or ram < 4 or temp_value > 80:
             time.sleep(60)
         return cpu, ram, temp_value
     ```

3. **Define Core Tools**:
   - Create modular functions for vision, speech, navigation, and signup:
     - **Vision**: `read_screen()` using EasyOCR to extract text from screenshots.
     - **Signup**: `signup_service(url)` to register on websites with Temp-Mail and Faker.
     - **Navigation**: Use Playwright/Selenium for browser control.
     - Example:
       ```python
       import easyocr, pyautogui, requests, faker
       reader = easyocr.Reader(['en'])
       fake = faker.Faker()
       def read_screen():
           screenshot = pyautogui.screenshot()
           return " ".join(reader.readtext(np.array(screenshot), detail=0))
       def signup_service(url):
           browser.get(url)
           text = read_screen()
           if "sign up" in text.lower():
               pyautogui.click(500, 500)  # Adjust based on OCR detection
           email = requests.get("https://api.temp-mail.org/request/mail").json()["email"]
           pyautogui.typewrite(email)
           pyautogui.typewrite(fake.password())
           pyautogui.press("enter")
           return f"Account created: {email}"
       ```

4. **Set Up the Agent**:
   - Configure the ZeroShotAgent with tools and integrate with `AgentExecutor`.
   - Example:
     ```python
     tools = [
         Tool(name="Vision", func=read_screen, description="Read screen text"),
         Tool(name="Signup", func=signup_service, description="Register on a service"),
         Tool(name="Web", func=lambda x: browser.get(x), description="Navigate to URL"),
     ]
     agent = ZeroShotAgent(llm=llm, tools=tools, memory=memory)
     executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)
     ```

5. **Main Execution Function**:
   - Implement `run_task(prompt)` to process user requests, check resources, and execute actions.
   - Example:
     ```python
     def run_task(prompt):
         check_resources()
         return executor.run(prompt)
     ```

6. **Add Proactive Logic**:
   - Use memory to suggest actions based on history, e.g., check past prompts and propose related tasks.
   - Example:
     ```python
     if "write" in memory.buffer.lower():
         print("Suggestion: Shall I set up Grammarly?")
     ```

7. **Ensure Security**:
   - Encrypt sensitive data (e.g., API keys) with OpenSSL and store in Keyring.
   - Example:
     ```python
     import os
     os.system("openssl enc -aes-256-cbc -in keys.txt -out keys.enc")
     ```

8. **Test with Examples**:
   - Include test cases like "Register me on Canva" or "Plan my day" to verify functionality.

### Code Guidelines
- **Modularity**: Break the code into functions (e.g., `read_screen`, `signup_service`) for reusability.
- **Comments**: Add detailed comments explaining each section (e.g., "Initialize browser for web navigation").
- **Error Handling**: Use try-except blocks to manage failures (e.g., network errors, OCR misreads).
- **Scalability**: Structure the code to allow future tool additions (e.g., new APIs).

### Example Output
For the prompt "Register me on Canva and create a visual":
- Polyad navigates to canva.com, reads the "Sign Up" button, registers with a temp email, retrieves an API key, and generates a design.

Generate a complete, well-commented Python script following these instructions. Ensure it’s optimized for the MacBook 2019’s constraints and delivers a robust, user-friendly "Genie Agent" experience.