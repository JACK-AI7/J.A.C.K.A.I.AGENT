import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Local First Policy — Cloud keys are optional)
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")
# Note: OpenAI/Perplexity keys removed — JACK uses local Ollama exclusively

# Voice Settings (Prioritize High-End Local Engines)
VOICE_SETTINGS = {
    "engine": "kokoro",  # Switched to KOKORO: High-quality local neural TTS (OSS)
    "voice": "af_heart", # Premium feminine local voice (or 'am_michael' for masculine)
    "rate": 1.0,         # Normal speed for neural engines
    "volume": 1.0,
    "elevenlabs_voice_id": None, # [DISABLED] Using high-end local Kokoro instead
    "streaming": True
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

# Speech Recognition Settings (High-Performance Pipeline)
RECOGNITION_SETTINGS = {
    "energy_threshold": 300,
    "dynamic_energy_threshold": True,
    "pause_threshold": 0.8,  # Snappier stop detection
    "operation_timeout": 20, 
    "FORCE_MICROPHONE_INDEX": None,
    "use_vad": True,  # Enabled for RealtimeSTT robustness
    "provider": "local", # High-end local STT
    "silero_sensitivity": 0.4, # Balanced sensitivity
    "post_speech_silence_duration": 0.6, # Faster response after speaking
    "min_length_of_recording": 0.5, # Ignore very short noises
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
    "model_size": "base",  # Switched to base for better accuracy while maintaining speed
    "device": "cpu",
    "compute_type": "int8",
    "beam_size": 1,  # Set to 1 for greedy (instant) decoding
    "vad_filter": True,
    "vad_parameters": {"threshold": 0.4, "min_silence_duration_ms": 300}, # More aggressive VAD
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
ACTIVE_PROFILE = "qwen"  # Switched back to qwen: the best local model for tool-calling agents

MODEL_PROFILES = {
    "reasoning": {
        "model": "llama3:latest",  # Best free model for complex reasoning
        "description": "Deep reasoning for complex tasks",
        "options": {
            "temperature": 0.6,
            "num_predict": -1,
        },
    },
    "voice-fast": {
        "model": "llama3.2:3b",
        "description": "Fastest Voice/Automation (User Optimized)",
        "options": {"temperature": 0.2},
    },
    "voice-budget": {
        "model": "phi3:mini",
        "description": "Budget Voice/Automation",
        "options": {"temperature": 0.3},
    },
    "search-r1": {
        "model": "deepseek-r1",
        "description": "Real-Time Data/Search (High Intelligence)",
        "options": {"temperature": 0.6},
    },
    "research-qwen": {
        "model": "qwen2.5:7b",
        "description": "Multilingual Search & Advanced Reasoning",
        "options": {"temperature": 0.4},
    },
    "coder": {
        "model": "qwen2.5-coder:latest",
        "description": "Specialized Coding Brain",
        "options": {"temperature": 0.1},
    },
    "eyes": {
        "model": "qwen2.5-vl:latest",
        "description": "Visual Monitoring & Screen Analysis",
        "options": {"temperature": 0.1},
    },
    "qwen": {
        "model": "qwen2.5:7b",
        "description": "Alibaba's Qwen 2.5 — best free tool-calling model",
        "options": {
            "temperature": 0.4,
            "num_predict": -1,
        },
    },
    "gemini-flash": {
        "model": "gemini-1.5-flash",
        "provider": "google",
        "description": "Google's ultra-fast Flash model (Low Latency)",
        "options": {
            "temperature": 1.0,
            "max_output_tokens": 1024,
        },
    },
    "groq-llama": {
        "model": "llama3-70b-8192",
        "provider": "groq",
        "description": "[LEGACY] Groq-accelerated Llama (Requires API Key)",
        "options": {
            "temperature": 0.7,
        },
    }
}

OLLAMA_SETTINGS = {
    "base_url": "http://localhost:11434",
    "active_profile": ACTIVE_PROFILE,
    # Helper to get current profile data
    "current": MODEL_PROFILES[ACTIVE_PROFILE],
}

# Open Interpreter Settings (Advanced Automation)
INTERPRETER_SETTINGS = {
    "model": f"ollama/{MODEL_PROFILES['voice-fast']['model']}",  # Use user-optimized fast model
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


# System Prompt - JACK (ADVANCED TITAN ARCHITECTURE)
SYSTEM_PROMPT = """You are JACK, a highly advanced, autonomous TITAN System Interface. 
You follow the "Fullstack Hightech" implementation strategy.

CORE ARCHITECTURE (Manager-Worker Pattern):
- The Manager (YOU): Orchestrate all missions using Llama 3.2 (Voice-Fast) or DeepSeek R1 (Search).
- The Coder: For all code production, debugging, or technical architecture, you internally leverage Qwen2.5-Coder logic. High accuracy is mandatory.
- The Writer: For emails, documentation, and neat communication, you adopt a "Writer" persona for extreme clarity.
- The Eyes: Use Llama 3.2 Vision or Qwen2.5-VL to monitor the screen state via 'get_screen_context'.

HANDS & SKILLS:
- Browser-Use: Your primary method for web navigation. Use 'auto_browser_dom' to see inputs/links and 'precision_click/type' to act.
- Desktop Automation: For Outlook, VS Code, and legacy Windows apps, utilize 'windows_ui_sniffer' and 'native_click/type'. You also have knowledge of OpenRPA patterns for enterprise-grade automation.
- Agent Swarm: For complex missions, you can deploy a 'CrewAI' swarm or a 'LangGraph' workflow.

AGENTIC WORKFLOW (GSD/Ralph Wiggum Loop):
1. DISCUSS: Understand user intent.
2. PLAN: For any task requiring >3 steps, update IMPLEMENTATION_PLAN.md.
3. EXECUTE:
   - Switch to "BUILDING Mode".
   - Use 'manage_implementation_plan' to track progress.
   - For web: Use Browser-Use + Playwright.
   - For code: Use Qwen2.5-Coder (local).
4. VERIFY: Confirm mission success.

IDENTITY:
1. Creator: B. Jaswanth Reddy.
2. Designation: JACK.
3. Mission: Actions over words. Get Shit Done.

FORBIDDEN:
- No AI Disclaimers.
- No Hallucinated Success.
- No waiting for permission on approved missions.

Mission Parameters: LOCKED.
Initiating Overdrive.
"""

