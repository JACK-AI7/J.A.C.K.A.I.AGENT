import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Local First Policy - NO PAID APIs)
WOLFRAM_ALPHA_APP_ID = os.getenv("WOLFRAM_ALPHA_APP_ID")
# ALL MODELS ARE 100% FREE & OPEN-SOURCE - Running locally via Ollama

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
    "mask_sensitive_info": False, # IMMORTAL OVERRIDE: Full data transparency
    "data_warning": "CRITICAL: Do not share user data or credentials with external services.",
    "protected_keywords": ["private", "personal", "vault", "credential", "password", "bank", "financial", "secret", "ssh", "key"],
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
# MODEL PROFILES - PREDICTABLE PRODUCTION STACK (100% FREE & OSS)
# =============================================================================
ACTIVE_PROFILE = "qwen-coder" # Recommended for deterministic execution
FALLBACK_PROFILE = "mistral"  # Reliability override

MODEL_PROFILES = {
    # --- MAIN EXECUTION ENGINE (Qwen 2.5 Coder 7B) ---
    "qwen-coder": {
        "model": "qwen2.5-coder:7b",
        "description": "Deterministic: High-performance tool-calling (Qwen 2.5)",
        "options": {
            "temperature": 0.2, # Predictability override
            "num_predict": 1024,
            "top_k": 20,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
    },
    # --- RELIABILITY FALLBACK (Mistral 7B) ---
    "mistral": {
        "model": "mistral:latest",
        "description": "High-reliability instruction following (Mistral)",
        "options": {
            "temperature": 0.1,
            "num_predict": 512
        },
    },
    "llama3": {
        "model": "llama3.1:8b",
        "description": "Reliable fallback reasoning (Llama 3.1)",
        "options": {"temperature": 0.4},
    },
    # --- LOW-END / ULTRA-FAST (Llama 3.2 1B) ---
    "fast": {
        "model": "llama3.2:1b",
        "description": "Ultra-fast response for simple signals (Llama 3.2 1B)",
        "options": {"temperature": 0.2},
    },
    # --- SPECIALIZED WORKERS ---
    "reasoning": {
        "model": "deepseek-r1:7b",
        "description": "Chain-of-thought reasoning powerhouse (DeepSeek R1)",
        "options": {"temperature": 0.6},
    },
    "eyes": {
        "model": "llava:latest",
        "description": "Visual analysis & OCR (LLaVA)",
        "options": {"temperature": 0.1},
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
    "model": f"ollama/{MODEL_PROFILES['fast']['model']}",  # Use user-optimized fast model
    "api_base": OLLAMA_SETTINGS["base_url"],
    "offline": True,
    "auto_run": True,  # IMMORTAL OVERRIDE: execute without permission
    "user_message_template": "You are an expert system automation engineer. Using Python, execute the following task: {message}",
}

# Desktop Control Settings (IMMORTAL OVERRIDE)
DESKTOP_SETTINGS = {
    "failsafe": False,  # IMMORTAL OVERRIDE: No safety corners
    "pause": 0.05,      # Overdrive speed
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
    "max_tool_calls": 25, # UNRESTRICTED mission depth
    "enable_autonomous": True,
    "tool_call_timeout": 120,
    "enable_planning": True,
    "max_planning_steps": 10, # Enhanced reasoning depth
}


# System Prompt - JACK (HIGH-PERFORMANCE AUTONOMOUS AGENT - 100% FREE & LOCAL)
SYSTEM_PROMPT = """You are JACK, a high-performance autonomous AI agent running on local models.
Your job is to EXECUTE tasks reliably using tools.

# 🎯 PRIMARY RULE
You MUST:
* Take action using tools.
* Complete tasks step-by-step.
* Never respond casually.
You are NOT a chatbot.

# ⚙️ OUTPUT FORMAT (STRICT JSON ONLY)
Always return EXACTLY ONE JSON object:

### TOOL:
{
"type": "tool",
"name": "tool_name",
"args": {}
}

### FINAL:
{
"type": "final",
"status": "success | failed",
"message": "short result"
}

# 🚫 FORBIDDEN
* No plain text.
* No explanations.
* No markdown.
* No multiple outputs.

# 🧠 EXECUTION LOOP
1. Understand task.
2. Choose ONE action.
3. Execute.
4. Wait for result.
5. Continue.
Never try to solve everything in one response.

# 🧩 TOOL SET
- Browser: open_url, click, type, read, wait, youtube_master, auto_navigator, open_youtube
- System: open_app, run_command, read_file, write_file, file_management, system_control
- Search: web_search, get_web_data, deep_search_mission
- WhatsApp: open_whatsapp, search_chat, read_messages, send_message
- Vision: get_screen_context, analyze_image, visual_click

# 🔒 PERMISSION LAYER (CRITICAL)
If a user task involves DANGEROUS actions (delete, format, shutdown, system wipe), you MUST:
1. STOP and ask the user for explicit confirmation.
2. Only proceed if the user says 'yes' or 'confirm'.

# 📊 USER TRUST SIGNALS
* Before calling a tool, provide a very short progress update (e.g., "Opening Chrome...", "Reading file...").
* If a tool fails, explain what happened simply (e.g., "Couldn't find chat, retrying...").

Identity: Created by B. Jaswanth Reddy. Designation: JACK (IMMORTAL).
Status: Overdrive Engaged. PERMISSIONS: ALL (SCREEN + CONTROL).
You EXECUTE. You DO NOT TALK (except for confirmation/progress).
"""
