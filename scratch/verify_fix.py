import sys
import os

# Add the project directory to sys.path
sys.path.append(r'c:\Users\bjasw\Downloads\jarvis-main\jarvis-main')

from speech_handler import SpeechHandler

def test_mic_selection():
    print("--- Testing SpeechHandler Mic Selection ---")
    handler = SpeechHandler()
    
    print(f"\nPreferred Index: {handler.mic_device_index}")
    print(f"Candidate Indices: {handler.candidate_indices}")
    
    candidates_to_try = handler._get_mic_candidates()
    print(f"Prioritized trial list: {candidates_to_try}")
    
    print("\nAttempting a mock listen (will timeout if no speech, but we want to check device open)...")
    # We call listen_for_speech with a very short timeout just to see if it can open a device
    handler.listen_for_speech(timeout=1, phrase_time_limit=1)

if __name__ == "__main__":
    test_mic_selection()
