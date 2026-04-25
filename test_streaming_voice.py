import os
import time
from dotenv import load_dotenv

# Load keys
load_dotenv()

# Add core to sys.path
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ["core", "agents", "gui", "utils", "setup"]:
    folder_path = os.path.join(script_dir, folder)
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)

from core.speech_handler import SpeechHandler
from core.ai_handler import AIHandler

def test_pipeline():
    print("=== JACK PREMIUM PIPELINE TEST ===")
    
    # 1. Initialize Handlers
    print("\n[1] Initializing Handlers...")
    try:
        speech = SpeechHandler()
        ai = AIHandler()
        print("Handlers Online.")
    except Exception as e:
        print(f"Init Failed: {e}")
        return

    # 2. Test VAD & ASR
    print("\n[2] Testing VAD & ASR...")
    print("Please say 'Hello Jack' in the next 5 seconds...")
    text = speech.listen_for_speech(timeout=5)
    
    if text:
        print(f"ASR Success: Captured '{text}'")
        
        # 3. Test AI Reasoning
        print("\n[3] Testing AI Reasoning (Gemini/Groq)...")
        response = ai.process_query(text)
        print(f"AI Response: {response}")
        
        # 4. Test TTS Streaming
        print("\n[4] Testing TTS Streaming (ElevenLabs)...")
        speech.speak(response)
    else:
        print("ASR Failed: No speech detected or API error.")

if __name__ == "__main__":
    # Check for keys first
    keys = ["GEMINI_API_KEY", "ELEVENLABS_API_KEY", "OPENAI_API_KEY"]
    missing = [k for k in keys if not os.getenv(k) or "your_" in (os.getenv(k) or "")]
    
    if missing:
        print(f"WARNING: The following keys are missing from .env: {', '.join(missing)}")
        print("The test will likely fallback to local Ollama/Offline TTS.")
    
    test_pipeline()
