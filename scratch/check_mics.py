import speech_recognition as sr
import re

def clean(name):
    return re.sub(r'[\r\n\x00-\x1f]', ' ', name).lower()

print("Scanning for NATIVE microphones ONLY...")
try:
    mics = sr.Microphone.list_microphone_names()
    target_keywords = ["microphone array", "mic array"]
    exclude_keywords = ["mapper", "headset", "hands-free", "bluetooth", "stereo mix", "speaker"]
    
    for i, name in enumerate(mics):
        clean_name = clean(name)
        is_target = any(k in clean_name for k in target_keywords)
        is_excluded = any(k in clean_name for k in exclude_keywords)
        
        status = "[TARGET]" if (is_target and not is_excluded) else "[IGNORE]"
        print(f"  {status} [{i}] {name}")

except Exception as e:
    print(f"Error: {e}")
