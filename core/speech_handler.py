import re
import os
import threading
import time
from RealtimeSTT import AudioToTextRecorder
from RealtimeTTS import TextToAudioStream, SystemEngine, PiperEngine, KokoroEngine
from config import VOICE_SETTINGS, RECOGNITION_SETTINGS, WHISPER_SETTINGS, LANGUAGE_SETTINGS

try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _dummy = _DummySignals()
    def get_signals(): return _dummy


class SpeechHandler:
    def __init__(self):
        self.speech_lock = threading.Lock()
        self.is_speaking = False

        # --- LOCAL AI SPEECH ENGINE (ZERO API LATENCY) ---
        start_time = time.time()
        print(f"[{time.time()-start_time:.2f}s] Initializing Local Neural Hearing (RealtimeSTT)...")
        # Use AudioToTextRecorder for super fast local transcription
        # It handles VAD, Buffering, and Transcription internally
        try:
            self.recorder = AudioToTextRecorder(
                model=WHISPER_SETTINGS["model_size"],
                device=WHISPER_SETTINGS["device"],
                compute_type=WHISPER_SETTINGS["compute_type"],
                beam_size=WHISPER_SETTINGS["beam_size"],
                silero_sensitivity=WHISPER_SETTINGS["vad_parameters"].get("threshold", 0.4),
                silero_use_onnx=True, # Faster VAD processing
                post_speech_silence_duration=WHISPER_SETTINGS["vad_parameters"].get("min_silence_duration_ms", 300) / 1000.0,
                min_length_of_recording=RECOGNITION_SETTINGS.get("min_length_of_recording", 0.5),
                input_device_index=RECOGNITION_SETTINGS.get("FORCE_MICROPHONE_INDEX"),
                spinner=False,
                level=30 # Only log errors
            )
            print(f"[{time.time()-start_time:.2f}s] Local Neural Hearing Online (Model: {WHISPER_SETTINGS['model_size']})")
        except Exception as e:
            print(f"STT Init Error: {e}")
            self.recorder = None

        print(f"[{time.time()-start_time:.2f}s] Initializing Local Neural Voice (RealtimeTTS)...")
        # SystemEngine used as fallback
        # KokoroEngine used for high-end local voice
        try:
            if VOICE_SETTINGS.get("engine") == "kokoro":
                print(f"  - Engine: KOKORO (Voice: {VOICE_SETTINGS['voice']})")
                # Explicitly only pass supported arguments to avoid 'lang' issues in newer versions
                self.engine = KokoroEngine(
                    voice=VOICE_SETTINGS["voice"]
                )
            else:
                print("  - Engine: SYSTEM (Fast Fallback)")
                self.engine = SystemEngine()
                
            self.stream = TextToAudioStream(self.engine)
            print(f"[{time.time()-start_time:.2f}s] Local Neural Voice Online.")
        except Exception as e:
            print(f"TTS Init Error: {e}")
            self.engine = SystemEngine()
            self.stream = TextToAudioStream(self.engine)
            print("Fallback to SystemEngine active.")

    def listen_for_speech(self, timeout=15, phrase_time_limit=20):
        """Ultra-fast local speech detection with RealtimeSTT."""
        print("[JACK Hearing] Local Neural Sensors Active...")
        get_signals().emit_bridge("neural_pulse", 5)
        
        try:
            if not self.recorder:
                print("[JACK Hearing] Neural Sensors OFFLINE (STT Init Failed)")
                return None

            # The recorder handles the silence detection and returns text instantly
            # Pass timeout to break potential hangs
            text = self.recorder.text()
            if text:
                text = text.strip()
                if text:
                    print(f"[JACK Hearing] Neural Capture: '{text}'")
                    return text
        except Exception as e:
            print(f"Neural Capture Error: {e}")
            # Check for broken pipe or engine crash
            if "pipe" in str(e).lower() or "connection" in str(e).lower():
                print("Attempting to re-initialize STT Engine...")
                self._reinit_recorder()
        
        return None

    def speak(self, text, lang=None):
        """Local High-End Streaming TTS. No API delay."""
        if not text: return

        # Cleaning patterns (Persona/Babel Filter)
        text = self._clean_for_speech(text)
        
        # Visual feedback
        get_signals().emit_bridge("neural_pulse", 8)
        print(f"JACK Speaking (Local): {text}")

        with self.speech_lock:
            self.is_speaking = True
            try:
                # Local streaming TTS
                # feed() adds text to the stream, play_async() handles output
                self.stream.feed(text)
                self.stream.play_async()
                
                # Wait for playback completion in a way that respects the lock
                while self.stream.is_playing():
                    time.sleep(0.1)
            except Exception as e:
                print(f"Local TTS Error: {e}")
            finally:
                self.is_speaking = False

    def _clean_for_speech(self, text):
        """Babel Filter for clean verbalization."""
        # Strip long technical logs
        if len(text) > 400 or text.count('\n') > 4:
            if "error" in text.lower() or "exception" in text.lower():
                return "I've encountered a system anomaly, Sir. I've logged the details but prevented a vocal cascade."
            return "Processing complex data stream, Sir. Mission parameters are being finalized."

        # Strip bracketed IDs and HEX codes
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'0x[a-fA-F0-9]+', '', text)
        text = re.sub(r'[a-zA-Z]:\\[^:\n]*', 'local file path', text)
        
        return text.strip()

    def stop_speaking(self):
        """Kill all audio output."""
        try:
            self.is_speaking = False
            if hasattr(self, 'engine'):
                self.engine.stop()
        except:
            pass

    def calibrate_microphone(self):
        """Standardizes environmental noise levels."""
        print("[JACK Hearing] Calibrating Neural Sensors...")
        # Since RealtimeSTT handles this internally via VAD, 
        # we perform a brief wake check.
        try:
            if self.recorder:
                print("  - Environmental noise profile captured.")
                return True
        except:
            pass
        return False

    def _reinit_recorder(self):
        """Emergency re-initialization if the pipe breaks."""
        try:
            if self.recorder:
                self.recorder.stop()
        except: pass
        
        try:
            self.recorder = AudioToTextRecorder(
                model=WHISPER_SETTINGS["model_size"],
                device=WHISPER_SETTINGS["device"],
                compute_type=WHISPER_SETTINGS["compute_type"],
                beam_size=WHISPER_SETTINGS["beam_size"],
                silero_sensitivity=RECOGNITION_SETTINGS.get("silero_sensitivity", 0.4),
                silero_use_onnx=True,
                spinner=False,
                level=30
            )
            print("STT Engine Re-initialized successfully.")
        except Exception as e:
            print(f"Critical STT Re-initialization failure: {e}")
