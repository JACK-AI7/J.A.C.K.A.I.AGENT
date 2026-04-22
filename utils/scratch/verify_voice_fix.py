import speech_recognition as sr
import os
import sys

# Add current directory to path so we can import from local files
sys.path.append(os.getcwd())

try:
    from speech_handler import SpeechHandler
    print("Testing SpeechHandler initialization...")
    handler = SpeechHandler()
    
    print("\nMicrophone Candidates detected by JACK:")
    for idx in handler.candidate_indices:
        print(f"Index {idx}: {sr.Microphone.list_microphone_names()[idx]}")
    
    if handler.mic_device_index is not None:
        print(f"\n[SUCCESS] JACK has locked onto: Index {handler.mic_device_index} ({sr.Microphone.list_microphone_names()[handler.mic_device_index]})")
    else:
        print("\n[FAILURE] JACK could not find a suitable system microphone.")
        
except Exception as e:
    print(f"Error during verification: {e}")
