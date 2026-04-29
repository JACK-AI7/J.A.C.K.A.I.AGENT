import sys
import os

# Add core to path
script_dir = r"c:\Users\bjasw\Downloads\jarvis-main\jarvis-main"
sys.path.insert(0, os.path.join(script_dir, "core"))

try:
    from config import MODEL_PROFILES, OLLAMA_SETTINGS
    import ollama
    
    print("Checking model availability in Ollama...")
    client = ollama.Client(host=OLLAMA_SETTINGS["base_url"])
    
    # Check models used in profiles
    profiles_to_check = ["qwen", "coder", "reasoning", "voice-fast"]
    
    for profile in profiles_to_check:
        model = MODEL_PROFILES[profile]["model"]
        print(f"Profile '{profile}' uses model: {model}")
        try:
            client.chat(model=model, messages=[{"role": "user", "content": "hi"}])
            print(f"  [SUCCESS] Model '{model}' is working.")
        except Exception as e:
            print(f"  [FAILURE] Model '{model}' error: {e}")

except Exception as e:
    print(f"Verification Error: {e}")
