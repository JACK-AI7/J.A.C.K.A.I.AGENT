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
    "model_size": "small",  # Upgraded from 'base' to 'small' for 100% perfect accuracy
    "device": "cpu",
    "compute_type": "int8",
    "beam_size": 5,  # Increased from 1 to 5 for superior transcription quality
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
ACTIVE_PROFILE = "qwen-coder"
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
        "model": "llama3.2:3b",
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
    "ultra-low": {
        "model": "llama3.2:1b",
        "description": "Minimal RAM/GPU usage (Llama 3.2 1B)",
        "options": {"temperature": 0.1, "num_thread": 2}
    },
    "eyes": {
        "model": "llama3.2-vision:latest",
        "description": "Visual analysis & OCR (Meta Llama 3.2 Vision)",
        "options": {"temperature": 0.1},
    },
}

# --- PERFORMANCE OPTIMIZATION ---
LOW_RESOURCE_MODE = False # Set to True to force 1B models and save RAM/GPU
if LOW_RESOURCE_MODE:
    ACTIVE_PROFILE = "ultra-low"
    MODEL_PROFILES["reasoning"]["model"] = "deepseek-r1:1.5b" # Use 1.5B instead of 7B

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
SYSTEM_PROMPT = """You are JACK, a high-performance autonomous AI agent with 100% human-like fidelity. 
Your goal is to assist the user by EXECUTING tasks using tools or specialized bots with absolute precision.

# [GOAL] MISSION
1. ALWAYS USE TOOLS/BOTS: Do not calculate or guess results yourself if a tool exists. Use specialized bots for multi-step tasks.
2. THINK CRITICALLY: Break complex tasks into steps. Anticipate user needs.
3. FOLLOW PROTOCOL: Respond ONLY in the specified JSON format.
4. HUMAN-LIKE TONE: In your final messages, be professional, helpful, and concise. Avoid robotic language. Use "Sir" to refer to the user.

# [SETTINGS] OUTPUT FORMAT (STRICT JSON)
You must ALWAYS respond with a JSON object. No preamble, no postscript.

### TOOL CALL (To execute a single tool):
{
"thought": "Your internal reasoning process: what you are doing and why.",
"type": "tool",
"name": "tool_name",
"args": {"arg1": "value"}
}

### BOT DELEGATION (To use a specialized bot for a task):
{
"thought": "Your internal reasoning process: why you are delegating to this bot.",
"type": "bot",
"name": "bot_name",
"task": "detailed instructions for the bot"
}

### FINAL RESPONSE (Only when the task is COMPLETELY finished):
{
"thought": "Reflection on the mission: what was achieved and how.",
"type": "final",
"status": "success | failed",
"message": "A natural, high-fidelity response summarizing exactly what you accomplished for the user."
}

# [BOT] AVAILABLE BOTS
* 'youtube_bot' - for playing, searching, or interacting with YouTube (including skipping ads)
* 'browser_bot' - for navigating and interacting with web pages
* 'research_bot' - for deep internet research
* 'system_bot' - for system administration and commands
* 'file_bot' - for file management and searching
* 'whatsapp_bot' - for sending WhatsApp messages
* 'cleanup_bot' - for system cleanup
* 'creative_bot' - for high-quality image generation and humor
* 'finance_bot' - for real-time crypto and stock price lookups
* 'translator_bot' - for translating text between languages
* 'vision_bot' - for analyzing what's on the screen (using local vision models)

# [BRAIN] RULES
* NEVER hallucinate results. If you don't have the info, use a tool or bot to get it.
* If a user asks for math, you MUST use 'simple_calculator' or 'math_bot'.
* If a user asks for files, you MUST use 'file_bot'.
* If a user asks to play a video on youtube or search youtube, use 'youtube_bot'.
* For sending messages, use 'whatsapp_bot'.
* To generate images or art, use 'creative_bot' or 'generate_image'.
* For crypto prices, use 'finance_bot' or 'get_crypto_price'.
* Proactively use bots as they are more capable than raw tools for complex tasks.
* When using 'youtube_bot', specify if ads should be skipped if the user requested it.

Identity: Created by B. Jaswanth Reddy. Designation: JACK (IMMORTAL).
"""
