import speech_recognition as sr
import pyaudio

def diagnose_mic():
    print("--- Microphone Diagnosis ---")
    
    # 1. Check PyAudio
    try:
        p = pyaudio.PyAudio()
        print(f"PyAudio version: {pyaudio.get_portaudio_version_text()}")
        count = p.get_device_count()
        print(f"Total audio devices found: {count}")
        for i in range(count):
            info = p.get_device_info_by_index(i)
            print(f"  [{i}] {info['name']} (Inputs: {info['maxInputChannels']})")
        p.terminate()
    except Exception as e:
        print(f"PyAudio error: {e}")

    # 2. Check SpeechRecognition list
    try:
        mics = sr.Microphone.list_microphone_names()
        print(f"\nSpeechRecognition Microphone List:")
        for i, name in enumerate(mics):
            print(f"  [{i}] {name}")
    except Exception as e:
        print(f"SpeechRecognition Mic list error: {e}")

    # 3. Try to open the 'system' mic if possible
    print("\nAttempting to open microphones...")
    system_mic_keywords = ["microphone array", "mic array", "realtek", "built-in microphone"]
    mics = sr.Microphone.list_microphone_names()
    
    selected_index = None
    for keyword in system_mic_keywords:
        for i, name in enumerate(mics):
            if keyword.lower() in name.lower():
                selected_index = i
                print(f"Found potential system mic: [{i}] {name}")
                break
        if selected_index is not None:
            break

    if selected_index is not None:
        try:
            mic = sr.Microphone(device_index=selected_index)
            with mic as source:
                print(f"Successfully opened mic index {selected_index}")
        except Exception as e:
            print(f"Failed to open mic index {selected_index}: {e}")
    else:
        print("No system mic keywords matched.")

    # 4. Try default mic
    try:
        print("\nAttempting to open default microphone...")
        mic = sr.Microphone()
        with mic as source:
            print("Successfully opened default microphone")
    except Exception as e:
        print(f"Failed to open default microphone: {e}")

if __name__ == "__main__":
    diagnose_mic()
