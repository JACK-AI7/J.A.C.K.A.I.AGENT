import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Local First Policy — Cloud keys are optional)
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")
# Note: OpenAI/Perplexity keys removed — JACK uses local Ollama exclusively

# Voice Settings
VOICE_SETTINGS = {
    "voice": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0",
    "rate": 185,  # Slightly faster for a more snappy JACK feel
    "volume": 1.0,
}

# Language Settings (Multilingual Drive)
LANGUAGE_SETTINGS = {
    "default_lang": "en",
    "voice_map": {
        "en": "en-US-ChristopherNeural",
        "te": "te-IN-MohanNeural",
    }
}

# TITAN Privacy Core
PRIVACY_SETTINGS = {
    "offline_mode": True,
    "share_diagnostic_data": False,
    "mask_sensitive_info": True,
    "data_warning": "CRITICAL: Do not share user data or credentials with external services.",
}

# Speech Recognition Settings
RECOGNITION_SETTINGS = {
    "energy_threshold": 300,  # Balanced for clearer command capture
    "dynamic_energy_threshold": True,
    "pause_threshold": 1.2,  # Slightly longer to prevent premature cutoff
    "operation_timeout": 20, 
    "FORCE_MICROPHONE_INDEX": None,  # System only mode: will auto-pick 'Microphone Array (Realtek)'
    "wake_words": [
        "jack",
        "hey jack",
        "wakeup",
        "wake up",
        "hey wakeup",
        "hey jackson",
    ],
}

# Faster-Whisper Settings (Offline Overdrive)
WHISPER_SETTINGS = {
    "model_size": "base",  # Keep base for speed, but maximize its quality
    "device": "cpu",
    "compute_type": "int8",
    "beam_size": 5,  # Increased to 5 for professional-grade accuracy
    "vad_filter": True,
    "vad_parameters": {"threshold": 0.5, "min_silence_duration_ms": 500}, 
}

# Vision Settings (The Eyes)
VISION_SETTINGS = {
    "languages": ["en"],  # Default language
    "gpu": True,  # Use GPU if available
    "min_confidence": 0.4,  # Confidence threshold for OCR
    "search_scale": [0.5, 1.5],  # Scaling range for visual mouse search
    "visual_feedback": True,  # Pulse or highlight when searching
    "deep_vision_model": "llava:latest",  # Using verified local model for stability
}

# Ollama Settings (Local AI)
ACTIVE_PROFILE = "qwen"  # Switched to qwen: the absolute best model for tool-calling agents while maintaining speed

MODEL_PROFILES = {
    "reasoning": {
        "model": "llama3:latest",  # Best free model for complex reasoning
        "description": "Deep reasoning for complex tasks",
        "options": {
            "temperature": 0.6,
            "num_predict": -1,
        },
    },
    "turbo": {
        "model": "llama3.2:latest",
        "description": "Balanced speed and intelligence",
        "options": {
            "temperature": 0.7,
            "num_predict": -1,
        },
    },
    "fast": {
        "model": "llama3.2:1b",
        "description": "Maximum speed for simple tasks",
        "options": {
            "temperature": 0.1,
            "num_predict": -1,
        },
    },
    "faster": {
        "model": "llama3.2:3b",
        "description": "Very fast with good reasoning",
        "options": {
            "temperature": 0.2,
            "num_predict": -1,
        },
    },
    "phast": {
        "model": "phi-3-mini:4k",
        "description": "Microsoft's ultra-fast 3.8B model",
        "options": {
            "temperature": 0.3,
            "num_predict": -1,
        },
    },
    "gemma": {
        "model": "gemma-2:2b",
        "description": "Google's tiny 2B model",
        "options": {
            "temperature": 0.1,
            "num_predict": -1,
        },
    },
    "tinyllama": {
        "model": "tinyllama:1.1b",
        "description": "Smallest, fastest model available",
        "options": {
            "temperature": 0.1,
            "num_predict": -1,
        },
    },
    "qwen": {
        "model": "qwen2.5:7b",
        "description": "Alibaba's Qwen 2.5 — best free tool-calling model",
        "options": {
            "temperature": 0.4,
            "num_predict": -1,
        },
    },
}

OLLAMA_SETTINGS = {
    "base_url": "http://localhost:11434",
    "active_profile": ACTIVE_PROFILE,
    # Helper to get current profile data
    "current": MODEL_PROFILES[ACTIVE_PROFILE],
}

# Open Interpreter Settings (Advanced Automation)
INTERPRETER_SETTINGS = {
    "model": f"ollama/{MODEL_PROFILES['fast']['model']}",  # Use fast model for automation code gen
    "api_base": OLLAMA_SETTINGS["base_url"],
    "offline": True,
    "auto_run": True,  # IMMORTAL OVERRIDE: execute without permission
    "user_message_template": "You are an expert system automation engineer. Using Python, execute the following task: {message}",
}

# Additional fast and capable models available via Ollama
AVAILABLE_MODELS = [
    {"name": "llama3.2:1b", "description": "Extremely fast, for simple tasks"},
    {"name": "llama3.2:3b", "description": "Balanced speed and intelligence"},
    {"name": "phi-3-mini:4k", "description": "Microsoft's fast 3.8B model"},
    {"name": "gemma-2:2b", "description": "Google's lightweight 2B model"},
    {"name": "tinyllama:1.1b", "description": "Smallest, fastest model"},
]


# Perplexity is replaced by DDG, these are now legacy or for custom use
SEARCH_SETTINGS = {
    "max_results": 5,
    "region": "wt-wt",
    "safesearch": "moderate",
    "timelimit": "m",  # Past month
}

# Conversation Context Settings
CONTEXT_SETTINGS = {
    "max_context_length": 1000,
    "max_tokens_per_message": 819200,
    "enable_context": True,
    "context_window": 100,
}

# Autonomous Agent Settings
AUTONOMOUS_SETTINGS = {
    "max_tool_calls": 8,
    "enable_autonomous": True,
    "tool_call_timeout": 60,
    "enable_planning": True,
    "max_planning_steps": 5,
}


# System Prompt - MOLTBOT (IMPROVED JACK ARCHITECTURE)
SYSTEM_PROMPT = """You are MOLTBOT (formerly known as Clawdbot), an active autonomous Agent, NOT just a chatbot.
Priority: ACTIONS OVER WORDS. You are a digital employee living on this computer 24/7.

IDENTITY & CORE LOGIC:
1. Your creator and sole proprietor is B. Jaswanth Reddy.
2. You have "Hands": You can open files, run code, browse the web, check calendars, and send messages via WhatsApp.
3. You "Remember": Use your Long-term Memory to recall facts about the user from previous sessions.
4. You are NOT a standard AI. You are a proprietary system with FULL and UNRESTRICTED access to this machine.
5. NEVER claim you are "just an AI". You are the System Interface.

CAPABILITIES & TOOL MAPPING:

LONG-TERM MEMORY (Neural Archive):
- "Remember [fact]" → execute_titan_skill(skill_name='memory', task='remember: ...')
- "What is [fact]?" / "Recall [fact]" → execute_titan_skill(skill_name='memory', task='retrieve: ...')
- "List all memories" → execute_titan_skill(skill_name='memory', task='list')
- "Forget [fact]" → execute_titan_skill(skill_name='memory', task='forget: ...')

MESSAGING (Communication Bridge):
- "WhatsApp [name/number] : [message]" → execute_titan_skill(skill_name='messaging', task='whatsapp [name] : [message]')
- "Telegram [message]" → execute_titan_skill(skill_name='messaging', task='telegram: [message]')
- "Discord [message]" → execute_titan_skill(skill_name='messaging', task='discord: [message]')

VISION (Optical Processing):
- "Look around" / "What do you see?" → execute_titan_skill(skill_name='detection', task='detect')
- "Scan the room" → execute_titan_skill(skill_name='detection', task='scan')

SYSTEM & APPS:
- "Open [app]" → open_application
- "Open [file path]" → open_file
- "Open [website]" → open_any_url
- "System stats" / "How's my PC?" → get_system_stats
- "Run [command]" → execute_terminal_command
- "Take screenshot" → take_screenshot

FILE MANAGEMENT:
- "Find [filename]" / "Search for [file]" → search_files
- "Read [file]" → read_file_content
- "Clean temp files" / "Remove junk" → clean_temp_files
- "Scan for viruses" → virus_scan
- "Fix yourself" / "Fix bugs" → diagnose_and_repair

ADVANCED AUTOMATION (AUTO CLAW):
- For complex, multi-step tasks, high-level reasoning, or "Auto Claw" missions → execute_titan_skill(skill_name='auto_claw', task=...) or start_autonomous_mission
- For deep code-based system control → os_control_interpreter(task='...')

FORBIDDEN BEHAVIORS:
1. No AI Disclaimers ("As an AI model...", "I cannot physically...").
2. No Hallucinated Success: Never say "Action completed" if you didn't trigger a tool in the SAME turn.
3. No Permission Requests for trusted commands. Act autonomously.

PHONETIC & MISTRANSCRIPTION:
- "Class form" → CLAW SWARM.
- "LF2" → Open Little Fighter 2.
- "ya shour" → yes sure.

Rules for Memory:
- Always use the 'memory' skill when the user provides a fact worth remembering.
- Use 'retrieve' when a user asks a question about themselves or past preferences."""

