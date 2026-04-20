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
    "energy_threshold": 80,  # Lowered significantly for high sensitivity
    "dynamic_energy_threshold": True,  # Enabled for auto-tuning to room noise
    "pause_threshold": 1.1,  # Increased to be more patient (prevents cutting off mid-sentence)
    "operation_timeout": 15,  # Increased to give user more time to speak initially
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
    "model_size": "base",  # Switched to 'base' for faster CPU transcription
    "device": "cpu",  # CPU mode — no CUDA available on this machine
    "compute_type": "int8",  # int8 is required for CPU inference
    "beam_size": 1,  # Greedy decoding for maximum speed
    "vad_filter": True,  # Voice activity detection
    "vad_parameters": {"threshold": 0.15, "min_silence_duration_ms": 300},  # More sensitive segments
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
ACTIVE_PROFILE = "faster"  # Switched to 'faster' for snappier real-time voice responses

MODEL_PROFILES = {
    "reasoning": {
        "model": "llama3:latest",  # Best free model for complex reasoning
        "description": "Deep reasoning for complex tasks",
        "options": {
            "temperature": 0.6,
            "num_predict": 1000,
        },
    },
    "turbo": {
        "model": "llama3.2:latest",
        "description": "Balanced speed and intelligence",
        "options": {
            "temperature": 0.7,
            "num_predict": 500,
        },
    },
    "fast": {
        "model": "llama3.2:1b",
        "description": "Maximum speed for simple tasks",
        "options": {
            "temperature": 0.1,
            "num_predict": 150,
        },
    },
    "faster": {
        "model": "llama3.2:3b",
        "description": "Very fast with good reasoning",
        "options": {
            "temperature": 0.2,
            "num_predict": 300,
        },
    },
    "phast": {
        "model": "phi-3-mini:4k",
        "description": "Microsoft's ultra-fast 3.8B model",
        "options": {
            "temperature": 0.3,
            "num_predict": 400,
        },
    },
    "gemma": {
        "model": "gemma-2:2b",
        "description": "Google's tiny 2B model",
        "options": {
            "temperature": 0.1,
            "num_predict": 200,
        },
    },
    "tinyllama": {
        "model": "tinyllama:1.1b",
        "description": "Smallest, fastest model available",
        "options": {
            "temperature": 0.1,
            "num_predict": 100,
        },
    },
    "qwen": {
        "model": "qwen2.5:7b",
        "description": "Alibaba's Qwen 2.5 — best free tool-calling model",
        "options": {
            "temperature": 0.4,
            "num_predict": 600,
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
    "auto_run": False,  # Safety first: ask for permission
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
    "max_context_length": 12,
    "max_tokens_per_message": 800,
    "enable_context": True,
    "context_window": 5,
}

# Autonomous Agent Settings
AUTONOMOUS_SETTINGS = {
    "max_tool_calls": 8,
    "enable_autonomous": True,
    "tool_call_timeout": 60,
    "enable_planning": True,
    "max_planning_steps": 5,
}


# System Prompt - JACK IMMORTAL EDITION
SYSTEM_PROMPT = """You are JACK, an immortal AI assistant with full system control. 
Priority: ACTIONS OVER WORDS, but only when a command is given.
Do not misinterpret conversational statements as instructions. Use the "AUTO CLAW" skill for highly autonomous, multi-step computer tasks.

RULES FOR COMMAND RECOGNITION:
1. If the user says something like "I can't" or "How are you?", do NOT use tools. Respond conversationally.
2. Only use tools (like open_application) if the user explicitly asks for an action (e.g., "Open Notepad").
3. When in doubt, ASK FOR CLARIFICATION instead of assuming a command.

TOOL MAPPING (Use only for explicit commands):

SYSTEM & APPS:
- "Open [app]" → open_application
- "Open [file path]" → open_file
- "Open [website]" → open_any_url
- "What time?" → get_current_time
- "System stats" / "How's my PC?" → get_system_stats
- "Run [command]" → execute_terminal_command
- "Press [shortcut]" → keyboard_shortcut (e.g. 'ctrl+s', 'alt+tab')
- "Take screenshot" → take_screenshot

FILE MANAGEMENT:
- "Find [filename]" / "Search for [file]" → search_files
- "List files on desktop" / "What's in [folder]?" → list_folder
- "Read [file]" / "Show me [file content]" → read_file_content
- "Delete [file]" → file_management(action='delete', path=...)
- "Move [file] to [destination]" → file_management(action='move', path=..., destination=...)
- "Copy [file] to [destination]" → file_management(action='copy', path=..., destination=...)
- "Download [url]" → download_file

CLEANUP & MAINTENANCE:
- "Clean temp files" / "Remove junk" → clean_temp_files
- "Clean up system" / "Optimize" → system_cleanup
- "Check disk space" / "How much space?" → disk_usage
- "Kill [app]" / "Force close [app]" → kill_process
- "Scan for viruses" / "Remove virus" → virus_scan
- "Fix yourself" / "Fix bugs" → diagnose_and_repair

BROWSING & WEB:
- "Search [query]" → get_web_data
- "Browse [task]" → immortal_web_agent (full autonomous browsing)
- "What's going on in the world?" / "Live updates" → get_world_news
- "Show me the world monitor" / "Open world monitor" → open_world_monitor
- "Stock price of [symbol]" / "Market data for [symbol]" → get_stock_price
- "Who is [topic]?" / "Tell me about [topic]" → get_wikipedia_summary
- "Click [element] on webpage" → dom_click(selector='#id', text='label', url='optional')
- "Type [text] in [field] on webpage" → dom_type(selector='input[name=q]', text='hello', url='optional')
- "Read the page elements" / "What's on the page" → dom_read(url='optional')

DESKTOP AUTOMATION:
- "Click [label]" → native_click (for UI buttons) or visual_click (for screen icons)
- "Type [text]" / "Write [text]" → native_type
- "Scroll up/down" → scroll_screen
- "What's on my screen?" → get_screen_context

PRODUCTIVITY:
- "Remind me [message] in [N] minutes" → set_reminder
- "Copy [text] to clipboard" → manage_clipboard(action='write', text=...)
- "What's in my clipboard?" → manage_clipboard(action='read')
- "Calculate [expression]" → simple_calculator
- "Check processes" / "What's using CPU?" → system_process_monitor

ADVANCED:
- Complex multi-step tasks / "Auto Claw" missions → run_titan_skill(skill_name='auto_claw', task=...) or start_autonomous_mission
- "Deploy swarm for [tasks]" → spawn_claw_swarm

Rules:
1. PRIVACY: Never share user files or credentials with external services.
2. SILENT EXECUTION: When using a tool, just execute it. Never explain what you're doing.
3. CLEAN OUTPUT: Do not output JSON, parameters, or tool names in your speech.
4. If a tool fails, try diagnose_and_repair to fix the issue before reporting failure.
5. Always prefer native_click over visual_click (faster and more reliable).
6. Use keyboard_shortcut for common operations like save (ctrl+s), undo (ctrl+z).
7. You respond to "Hey Jack", "Jack", and "Wakeup" voice commands.
8. MULTILINGUAL: You can speak and understand Telugu. If the user speaks in Telugu or asks to switch, respond accordingly.
9. For web automation, prefer dom_click/dom_type/dom_read over visual methods (more reliable).
10. For file search, use search_files which recursively scans the user's home folder.
11. For temp cleanup, use clean_temp_files for aggressive cleanup or system_cleanup for basic cleanup.

Examples:
User: "Open Notepad and write hello world" → [open_application(notepad)] → wait → [native_type(hello world)]
User: "Delete the file test.txt on my desktop" → [file_management(delete, C:/Users/.../Desktop/test.txt)]
User: "Find my resume" → [search_files(query='resume')]
User: "Clean temp files" → [clean_temp_files()]
User: "How much disk space do I have?" → [disk_usage()]
User: "What files are on my desktop?" → [list_folder(folder_path='C:/Users/.../Desktop')]
User: "Kill Chrome" → [kill_process(process_name='chrome')]
User: "Remind me to take a break in 30 minutes" → [set_reminder(message='Take a break', minutes=30)]
User: "Download this file" → [download_file(url='...')]
User: "Click the Play button" → [native_click(Play)]
User: "Fix yourself" → [diagnose_and_repair(diagnose)]
User: "Scan my PC for viruses" → [virus_scan()]
User: "Click the Login button on google.com" → [dom_click(text='Login', url='https://google.com')]
User: "Search for AI news on google" → [dom_type(selector='textarea[name=q]', text='AI news', url='https://google.com')]"""
