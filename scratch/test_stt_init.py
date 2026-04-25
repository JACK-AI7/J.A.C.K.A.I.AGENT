from RealtimeSTT import AudioToTextRecorder
import time

try:
    print("Initializing AudioToTextRecorder with default settings...")
    recorder = AudioToTextRecorder(level=30)
    print("Recorder initialized successfully!")
    recorder.stop()
except Exception as e:
    print(f"Failed to initialize recorder: {e}")

print("\nTrying to find a valid device index...")
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info.get('maxInputChannels') > 0:
        name = info.get('name')
        print(f"Testing Index {i}: {name}")
        try:
            recorder = AudioToTextRecorder(input_device_index=i, level=30)
            print(f"  SUCCESS with Index {i}")
            recorder.stop()
            break
        except Exception as e:
            print(f"  FAILED Index {i}: {e}")
p.terminate()
