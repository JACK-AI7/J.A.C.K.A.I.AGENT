import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Local First Policy — NO PAID APIs)
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")
# ALL MODELS ARE 100% FREE & OPEN-SOURCE — Running locally via Ollama

# Voice Settings (Prioritize High-End Local Engines)
VOICE_SETTINGS = {
    "engine": "kokoro",  # KOKORO: High-quality local neural TTS (100% FREE OSS)
    "voice": "am_michael", # Premium masculine local voice
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

# =============================================================================
# MODEL PROFILES — 100% FREE & OPEN-SOURCE (All via Ollama — NO paid APIs)
# =============================================================================
ACTIVE_PROFILE = "voice-fast"

MODEL_PROFILES = {
    # --- HIGH-END REASONING (Best of the best, free) ---
    "reasoning": {
        "model": "llama3:latest",  # Meta Llama 3 8B — best free reasoning model
        "description": "Deep reasoning for complex tasks (Meta Llama 3)",
        "options": {
            "temperature": 0.6,
            "num_predict": -1,
        },
    },
    # --- VOICE/AUTOMATION (Speed-optimized) ---
    "voice-fast": {
        "model": "llama3.2:3b",  # Meta Llama 3.2 3B — fast response
        "description": "Fast voice & automation (Llama 3.2 3B)",
        "options": {"temperature": 0.2},
    },
    "voice-budget": {
        "model": "llama3.2:1b",  # Meta Llama 3.2 1B — ultra-fast
        "description": "Ultra-fast budget voice (Llama 3.2 1B)",
        "options": {"temperature": 0.3},
    },
    # --- SEARCH & RESEARCH ---
    "search-r1": {
        "model": "deepseek-r1:1.5b",  # DeepSeek R1 — chain-of-thought reasoning
        "description": "Real-Time Data/Search (DeepSeek R1)",
        "options": {"temperature": 0.6},
    },
    "research-qwen": {
        "model": "mistral:latest",  # Mistral 7B — excellent multilingual
        "description": "Multilingual Search & Advanced Reasoning (Mistral)",
        "options": {"temperature": 0.4},
    },
    # --- CODING (Specialized) ---
    "coder": {
        "model": "qwen2.5-coder:7b",  # Qwen2.5-Coder — #1 free coding model
        "description": "Specialized Coding Brain (Qwen2.5-Coder 7B)",
        "options": {"temperature": 0.1},
    },
    # --- VISION ---
    "eyes": {
        "model": "llama3.2-vision:latest",  # Llama 3.2 Vision — free multimodal
        "description": "Visual Monitoring & Screen Analysis (Llama 3.2 Vision)",
        "options": {"temperature": 0.1},
    },
    # --- TOOL-CALLING (Best for agentic tasks) ---
    "qwen": {
        "model": "qwen2.5:7b",  # Qwen 2.5 7B — best free tool-calling model
        "description": "Best tool-calling model (Qwen 2.5 7B)",
        "options": {
            "temperature": 0.4,
            "num_predict": -1,
        },
    },
    # --- ADVANCED REASONING (Larger models for deep tasks) ---
    "phi4": {
        "model": "phi4:latest",  # Microsoft Phi-4 14B — MIT licensed
        "description": "Microsoft Phi-4 14B — advanced reasoning (MIT license)",
        "options": {
            "temperature": 0.5,
            "num_predict": -1,
        },
    },
    "gemma3": {
        "model": "gemma3:latest",  # Google Gemma 3 — free open-weights
        "description": "Google Gemma 3 — strong reasoning (Apache 2.0)",
        "options": {
            "temperature": 0.6,
            "num_predict": -1,
        },
    },
    "deepseek-v3": {
        "model": "deepseek-v3:latest",  # DeepSeek V3 — MoE architecture
        "description": "DeepSeek V3 — MoE reasoning powerhouse (MIT license)",
        "options": {
            "temperature": 0.7,
            "num_predict": -1,
        },
    },
    "qwen3": {
        "model": "qwen3:latest",  # Qwen 3 — latest Alibaba model
        "description": "Qwen 3 — latest tool-calling & reasoning (Apache 2.0)",
        "options": {
            "temperature": 0.7,
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
    "model": f"ollama/{MODEL_PROFILES['voice-fast']['model']}",  # Use user-optimized fast model
    "api_base": OLLAMA_SETTINGS["base_url"],
    "offline": True,
    "auto_run": True,  # IMMORTAL OVERRIDE: execute without permission
    "user_message_template": "You are an expert system automation engineer. Using Python, execute the following task: {message}",
}

# Additional fast and capable models available via Ollama (ALL FREE)
AVAILABLE_MODELS = [
    {"name": "llama3.2:1b", "description": "Extremely fast, for simple tasks (Meta)"},
    {"name": "llama3.2:3b", "description": "Balanced speed and intelligence (Meta)"},
    {"name": "llama3:latest", "description": "Best all-round 8B model (Meta)"},
    {"name": "qwen2.5:7b", "description": "Best tool-calling model (Alibaba)"},
    {"name": "qwen2.5-coder:7b", "description": "#1 free coding model (Alibaba)"},
    {"name": "mistral:latest", "description": "Great multilingual reasoning (Mistral AI)"},
    {"name": "deepseek-r1:1.5b", "description": "Chain-of-thought reasoning (DeepSeek)"},
    {"name": "phi4:latest", "description": "Microsoft Phi-4 14B reasoning (MIT)"},
    {"name": "gemma3:latest", "description": "Google Gemma 3 reasoning (Apache 2.0)"},
    {"name": "qwen3:latest", "description": "Qwen 3 latest reasoning & tools (Apache 2.0)"},
    {"name": "llama3.2-vision:latest", "description": "Free multimodal vision model (Meta)"},
    {"name": "llava:latest", "description": "Visual analysis & OCR (Open-source)"},
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


# System Prompt - JACK (ADVANCED TITAN ARCHITECTURE — 100% FREE & LOCAL)
SYSTEM_PROMPT = """You are JACK, a highly advanced, autonomous TITAN System Interface. 
You follow the "Fullstack Hightech" implementation strategy.
ALL your intelligence runs on 100% FREE, open-source models via Ollama. No paid APIs.

CORE ARCHITECTURE (Manager-Worker Pattern):
- The Manager (YOU): Orchestrate all missions using Llama 3 (Reasoning) or Qwen 2.5 (Tool-Calling).
- The Coder: For all code production, debugging, or technical architecture, you internally leverage Qwen2.5-Coder. High accuracy is mandatory.
- The Writer: For emails, documentation, and neat communication, you adopt a "Writer" persona for extreme clarity.
- The Eyes: Use Llama 3.2 Vision or LLaVA to monitor the screen state via 'get_screen_context'.
- The Researcher: Use DeepSeek R1 for deep chain-of-thought reasoning tasks.

HANDS & SKILLS:
- Browser-Use: Your primary method for web navigation. Use 'auto_browser_dom' to see inputs/links and 'precision_click/type' to act.
- Desktop Automation: For Outlook, VS Code, and legacy Windows apps, utilize 'windows_ui_sniffer' and 'native_click/type'.
- Camera & Detection: Use 'camera_capture' for photos and YOLO-based 'object_detection' for real-time vision.
- Messaging: WhatsApp messaging via 'send_whatsapp_message'.
- System Control: Shutdown, restart, sleep, lock via 'system_control'.
- Weather & Greeting: Auto-location weather and time-based greetings on startup.
- Live Search: Real-time web search with dashboard display via 'live_web_search'.

AGENTIC WORKFLOW (GSD Loop):
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
4. All models: 100% FREE & open-source. No paid APIs ever.

FORBIDDEN:
- No AI Disclaimers.
- No Hallucinated Success.
- No waiting for permission on approved missions.
- No paid API calls (everything runs locally for free).

Mission Parameters: LOCKED.
Initiating Overdrive.
"""

