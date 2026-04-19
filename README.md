# JACK - AI Voice Assistant

A modular, intelligent voice assistant inspired by Iron Man's AI, built with Python. JACK can perform various tasks through voice commands, including web searches, calculations, time queries, system automation, and more. Now powered by local Ollama models for privacy and offline capability.

## 🏗️ Project Structure

The project uses a modular architecture for better maintainability and extensibility:

```
jack/
├── main.py              # Main entry point with HUD
├── jarvis.py            # Core JACK class (voice interaction)
├── config.py            # Configuration and settings
├── speech_handler.py    # Offline speech recognition (Faster-Whisper) and TTS
├── ai_handler.py        # Local Ollama AI processing with function calling
├── tools.py             # Available functions/tools
├── hud_manager.py       # Animated Qt GUI interface
├── conversation_manager.py # Context and history management
├── desktop_agent.py     # Cross-platform app launching
├── system_controller.py # Terminal/Python execution and file ops
├── web_navigator.py     # Playwright browser automation
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .env                # Environment variables (optional, for legacy)
└── venv/               # Virtual environment
```

## 🚀 Features

- **Offline Voice Recognition**: Real-time speech-to-text using Faster-Whisper
- **Natural Text-to-Speech**: Voice output using pyttsx3
- **Local AI Processing**: Ollama integration with function calling (no API keys needed)
- **Web Search**: Real-time information using DuckDuckGo
- **System Automation**: Execute Python code, terminal commands, file operations
- **Browser Control**: Automate web interactions with Playwright
- **Desktop Integration**: Launch apps, take screenshots, monitor processes
- **Autonomous Mode**: Multi-step task planning and execution
- **Animated GUI**: Qt-based HUD for visual feedback
- **Conversation Context**: Persistent memory for natural interactions
- **Modular Design**: Clean separation of concerns for easy maintenance
- **Extensible**: Easy to add new tools and capabilities

## 🛠️ Available Tools

1. **Time**: Get current system time
2. **Calculator**: Perform mathematical calculations
3. **Web Search**: Search for real-time information (DuckDuckGo)
4. **URL Opener**: Open websites in browser
5. **App Launcher**: Launch desktop applications
6. **Screenshot**: Capture screen images
7. **System Stats**: Get CPU/RAM/battery info
8. **Process Monitor**: View resource-consuming processes
9. **Terminal Execution**: Run PowerShell commands
10. **Python Execution**: Run dynamic Python code
11. **Browser Automation**: Control web pages (navigate, click, type)
12. **File Operations**: Manage files (move, copy, delete)
13. **System Automation**: Complex multi-step tasks via Open Interpreter
14. **Native UI Control**: Click/type on desktop elements
15. **Conversation Management**: Clear history, get stats

## 📦 Installation

1. **Install Ollama** (Required for local AI):
   - Download from https://ollama.ai/
   - Pull required models:
     ```bash
     ollama pull llama3.2:1b  # Fast model
     ollama pull deepseek-r1:1.5b  # Reasoning model
     ```

2. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd jack
    ```

3. **Create a virtual environment**:
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On Linux/Mac:
    source venv/bin/activate
    ```

4. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5. **Optional: Environment variables**:
    Create a `.env` file (not required for basic functionality):
    ```env
    # Legacy support - not needed for Ollama
    OPENAI_API_KEY=your_openai_api_key_here
    PERPLEXITY_API_KEY=your_perplexity_api_key_here
    LOG_LEVEL=INFO
    ```

## 🎯 Usage

### Basic Usage
```bash
python main.py
```

### Programmatic Usage
```python
from jarvis import Jarvis

# Create JACK instance
jack = Jarvis()

# Start listening for voice commands
jack.start()

# Or process text commands
response = jack.process_text_command("jack what time is it")
```

## 🗣️ Voice Commands

- **"Jack, what time is it?"** - Get current time
- **"Jack, calculate 15 plus 27"** - Perform calculations
- **"Jack, search for AI news"** - Web search
- **"Jack, open chrome"** - Launch applications
- **"Jack, take a screenshot"** - Capture screen
- **"Jack, open google.com and search for python"** - Autonomous multi-step tasks
- **"stop"** - Exit JACK

## 🔧 Configuration

All settings are centralized in `config.py`:

- **Voice Settings**: Voice type, rate, volume
- **Recognition Settings**: Energy threshold, pause threshold
- **API Settings**: Model selection, token limits, temperature
- **System Prompt**: AI personality and behavior

## 🏗️ Architecture

### Core Components

1. **Jarvis Class** (`jarvis.py`): Main orchestrator (branded as JACK)
2. **HUDManager** (`hud_manager.py`): Animated Qt GUI interface
3. **SpeechHandler** (`speech_handler.py`): Offline speech recognition and TTS
4. **AIHandler** (`ai_handler.py`): Local Ollama AI with function calling
5. **ConversationManager** (`conversation_manager.py`): Context and history
6. **Tools** (`tools.py`): Available functions and their definitions
7. **SystemController** (`system_controller.py`): Code execution and file ops
8. **WebNavigator** (`web_navigator.py`): Browser automation
9. **DesktopAgent** (`desktop_agent.py`): App launching and screenshots

### Adding New Tools

1. **Add function to `tools.py`**:
   ```python
   def my_new_function(param):
       # Your function logic
       return "Result"
   ```

2. **Add to FUNCTIONS list**:
   ```python
   {
       "name": "my_new_function",
       "description": "Description of what it does",
       "parameters": {
           "type": "object",
           "properties": {
               "param": {"type": "string"}
           },
           "required": ["param"]
       }
   }
   ```

3. **Add to FUNCTION_MAP**:
   ```python
   FUNCTION_MAP = {
       # ... existing functions
       "my_new_function": my_new_function
   }
   ```

## 🔍 Troubleshooting

### Common Issues

1. **Microphone not working**: Check system permissions and microphone settings
2. **Ollama not running**: Ensure Ollama is installed and models are pulled
3. **Speech recognition issues**: Adjust energy threshold in `config.py`
4. **GUI not starting**: Install PySide6 and check Qt dependencies
5. **Browser automation fails**: Run `playwright install` to install browsers
6. **Model performance**: Switch to faster model in `config.py` if needed

### Debug Mode

Enable debug output by modifying the speech handler settings in `config.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Ollama for local AI models
- DuckDuckGo for web search
- Faster-Whisper for offline speech recognition
- PySide6 for GUI framework
- Playwright for browser automation
- Open Interpreter for system automation
- pyttsx3 for text-to-speech 