import re
import os
import speech_recognition as sr
import pyttsx3
import torch
import numpy as np
from faster_whisper import WhisperModel
from config import VOICE_SETTINGS, RECOGNITION_SETTINGS, WHISPER_SETTINGS, LANGUAGE_SETTINGS
import asyncio
import edge_tts
import pygame
import threading
import tempfile
import time
try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _dummy = _DummySignals()
    def get_signals(): return _dummy


class SpeechHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.speech_lock = threading.Lock()

        # Initialize Speech Engines
        self.use_whisper = False
        self.use_premium_voice = True

        # Initialize Pygame for stable audio playback
        try:
            pygame.mixer.init()
        except:
            pass

        # Initialize Fallback Engine (pyttsx3)
        try:
            self.offline_engine = pyttsx3.init()
            self.offline_engine.setProperty("voice", VOICE_SETTINGS["voice"])
            self.offline_engine.setProperty("rate", VOICE_SETTINGS["rate"])
        except:
            pass

        # Configure recognition settings - Optimized for stability
        self.recognizer.energy_threshold = RECOGNITION_SETTINGS["energy_threshold"]
        self.recognizer.dynamic_energy_threshold = RECOGNITION_SETTINGS[
            "dynamic_energy_threshold"
        ]
        self.recognizer.pause_threshold = RECOGNITION_SETTINGS["pause_threshold"]
        self.recognizer.operation_timeout = RECOGNITION_SETTINGS["operation_timeout"]

        # Initialize Local Whisper Engine
        print(f"Initializing Local Hearing ({WHISPER_SETTINGS['model_size']})...")
        try:
            self.whisper_model = WhisperModel(
                WHISPER_SETTINGS["model_size"],
                device=WHISPER_SETTINGS["device"],
                compute_type=WHISPER_SETTINGS["compute_type"],
            )
            print("Local Hearing Online.")
            self.use_whisper = True
        except Exception as e:
            print(f"Whisper Init failed: {e}")
            # Try fallback to CPU if GPU was requested and failed
            if WHISPER_SETTINGS["device"] != "cpu":
                print("Trying CPU fallback...")
                try:
                    self.whisper_model = WhisperModel(
                        WHISPER_SETTINGS["model_size"],
                        device="cpu",
                        compute_type="int8",  # float16 only works on GPU
                    )
                    print("Local Hearing (CPU) Online.")
                    self.use_whisper = True
                except Exception as e2:
                    print(f"CPU fallback failed: {e2}")
                    self.use_whisper = False
            else:
                self.use_whisper = False

        # System Microphone Setup — use the high-quality built-in system mic only
        # No Bluetooth/headset priority: always pick the Realtek Microphone Array or OS default
        self.mic_device_index = RECOGNITION_SETTINGS.get("FORCE_MICROPHONE_INDEX")
        self.candidate_indices = []
        
        if self.mic_device_index is not None:
            print(f"JACK Hearing: FORCED microphone index {self.mic_device_index}")
        else:
            try:
                import re as _re
                mics = sr.Microphone.list_microphone_names()

                def _clean(name):
                    return _re.sub(r'[\r\n\x00-\x1f]', ' ', name).lower()

                # Target the system's high-quality built-in microphone directly
                # Completely ignore headsets/Bluetooth buds as per user request for device mic only
                # Target the hardware-native "Microphone Array" ONLY as per user directive.
                # This excludes headsets, mappers, and virtual devices to ensure JACK uses "its own" mic.
                target_keywords = ["microphone array", "mic array"]
                exclude_keywords = ["mapper", "headset", "hands-free", "bluetooth", "stereo mix", "speaker"]
                
                print("JACK Hearing: Scanning for NATIVE system microphone ONLY...")
                for i, name in enumerate(mics):
                    clean_name = _clean(name)
                    is_target = any(k in clean_name for k in target_keywords)
                    is_excluded = any(k in clean_name for k in exclude_keywords)
                    
                    if is_target and not is_excluded:
                        self.candidate_indices.append(i)
                        print(f"  [+] TARGET DETECTED [{i}] {repr(name)}")
                    else:
                        print(f"  [ ] IGNORED device [{i}] {repr(name)}")

                if self.candidate_indices:
                    # Pick the primary hardware array (usually index 1 or 5 on this system)
                    self.mic_device_index = self.candidate_indices[0]
                    print(f"JACK Hearing: Locked to native mic [{self.mic_device_index}]")
                else:
                    print("JACK Hearing: WARNING: No native Microphone Array found. Using OS default.")
            except Exception as e:
                print(f"JACK Hearing Critical: Mic scan error ({e})")

    
    def _get_mic_candidates(self):
        """Return a list of indices to try, prioritized by preference."""
        indices = []
        if self.mic_device_index is not None:
            indices.append(self.mic_device_index)
        for idx in self.candidate_indices:
            if idx not in indices:
                indices.append(idx)
        # Always include None as the final fallback
        if None not in indices:
            indices.append(None)
        return indices

    def calibrate_microphone(self, duration=1.0):
        print(f"Calibrating microphone for ambient noise (duration={duration}s)...")
        for idx in self._get_mic_candidates():
            try:
                mic = sr.Microphone(device_index=idx) if idx is not None else sr.Microphone()
                with mic as source:
                    print(f"[SpeechHandler] Calibrating on index {idx}...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                    if self.recognizer.energy_threshold < 50:
                        self.recognizer.energy_threshold = 50
                    print(f"[SpeechHandler] Calibration complete. Energy threshold: {self.recognizer.energy_threshold}")
                    return True
            except Exception as e:
                print(f"Calibration failed on index {idx}: {e}")
                continue
        print("All calibration attempts failed. JACK will use default sensitivity.")
        return False

    def listen_for_speech(self, timeout=15, phrase_time_limit=20):
        """Listen for speech input with robust device retry logic."""
        audio_data = None
        
        for idx in self._get_mic_candidates():
            try:
                print(f"[SpeechHandler] Attempting listen on index {idx}...")
                mic = sr.Microphone(device_index=idx) if idx is not None else sr.Microphone()
                
                with mic as source:
                    print("[SpeechHandler] Listening...")
                    try: get_signals().emit_bridge("neural_pulse", 3)
                    except: pass
                    
                    if hasattr(self.recognizer, "dynamic_energy_threshold"):
                        self.recognizer.dynamic_energy_threshold = RECOGNITION_SETTINGS.get("dynamic_energy_threshold", False)
                    
                    audio_data = self.recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_time_limit
                    )
                    print("[SpeechHandler] Audio captured successfully.")
                    # If we got here, this mic worked! Update preferred index if it wasn't already set
                    if self.mic_device_index is None and idx is not None:
                        self.mic_device_index = idx
                    break # Success!
                    
            except (AttributeError, OSError, sr.WaitTimeoutError) as e:
                if isinstance(e, sr.WaitTimeoutError):
                    print("[SpeechHandler] No speech detected (WaitTimeoutError).")
                    return None
                print(f"[SpeechHandler] Mic index {idx} failed/busy: {e}. Trying next...")
                continue
        
        if audio_data is None:
            print("[SpeechHandler] Failed to capture audio from any microphone.")
            import time; time.sleep(1)
            return None

        try:
            # Visual feedback for transcription
            try: get_signals().emit_bridge("neural_pulse", 6)
            except: pass
            
            # 2. Transcribe Using Local Model (Whisper) or Fallback
            if self.use_whisper:
                # Direct numpy resample — much faster and more accurate than temp file bouncing
                try:
                    wav_data = (
                        np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
                        .flatten()
                        .astype(np.float32)
                        / 32768.0
                    )
                    
                    segments_iter, info = self.whisper_model.transcribe(
                        wav_data,
                        beam_size=WHISPER_SETTINGS.get("beam_size", 5),
                        vad_filter=WHISPER_SETTINGS.get("vad_filter", True),
                        vad_parameters=WHISPER_SETTINGS.get("vad_parameters", dict(min_silence_duration_ms=500)),
                        condition_on_previous_text=False  # Blocks hallucination death spirals on silence
                    )
                    segments_list = list(segments_iter)
                except Exception as e:
                    print(f"[SpeechHandler] Whisper transcription failed: {e}")
                    return None

                # If the AI strongly believes it was just noise, ignore it
                if getattr(info, 'no_speech_prob', 0) > 0.7:
                    print(f"[SpeechHandler] Ignored audio (No speech probability: {info.no_speech_prob})")
                    return None

                text = "".join(s.text for s in segments_list).strip()
                print(f"[SpeechHandler] Whisper transcription: '{text}'")
                return text if text else None
            else:
                # Basic Fallback (Google) if Whisper is not loaded
                print("[SpeechHandler] Using Google recognition (fallback)")
                return self.recognizer.recognize_google(audio_data)
        except sr.WaitTimeoutError:
            print(
                "[SpeechHandler] WaitTimeoutError - no speech detected within timeout"
            )
            return None
        except Exception as e:
            print(f"[SpeechHandler] Exception: {e}")
            if "UnknownValueError" not in str(e):
                print(f"Hearing Engine Exception: {e}")
            import time; time.sleep(2)  # Prevent CPU spin on persistent errors
            return None

    def speak(self, text, lang=None):
        """Convert text to speech with Premium-to-Offline fallback and Babel Filter."""
        if not text:
            return

        # --- THE BABEL FILTER (NUCLEAR EDITION) ---
        # Detect and block technical sequences, file paths, and logs
        technical_patterns = [
            r"\[\d+\]",  # [0], [1] list markers
            r"0x[a-fA-F0-9]+",  # Memory addresses or hex IDs
            r"\{[\s\S]*\}", # Raw JSON blocks
            r"[a-zA-Z]:\\[^:\n]*",  # Windows file paths (C:\Users\)
            r"Exception:", r"Traceback \(" , # Python errors
            r"---INTERNAL_REASONING_ONLY---",  # internal marker
            r"(\w+:\s*){2,}",  # Double colons (typical of lists or dicts)
            r"function call:", r"args:", r"kwargs:" # Tool leakage
        ]

        # Forbidden Words that trigger a total silence/fallback
        forbidden_words = [
            "button",
            "control",
            "parameter",
            "argument",
            "automation",
            "description",
            "id",
            "sniff",
        ]

        # Check for technical patterns
        for pattern in technical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Trigger a cleaner summary ONLY if the text is exceptionally long or complex
                # Increased threshold to allow more descriptive technical status from agents
                if len(text) > 400 or text.count('\n') > 4:
                    print(f"BABEL FILTER: Refining long technical sequence in speech.")
                    text = "I've analyzed the system data, Sir. Proceeding with the mission."
                    break

        # Physical Strip of Forbidden Words
        for word in forbidden_words:
            # Replaces variants (e.g., buttons, identifying) with empty space or clean alternatives
            pattern = re.compile(rf"\b{word}\w*\b", re.IGNORECASE)
            if pattern.search(text):
                print(f"NUCLEAR STRIP: Removing forbidden word '{word}' from speech.")
                text = pattern.sub("", text)

        # Final cleanup for punctuation artifacts after stripping
        text = re.sub(r"\s+", " ", text).strip(",. ")

        if not text or len(text.strip()) < 2:
            text = "Action synchronized, Sir."

        # Limit speech length for logs that missed patterns
        # Limit speech length for logs that missed patterns
        if text.count("\n") > 3 or len(text) > 350:
            original_len = len(text)
            # Truncate at nearest word
            text = text[:300].rsplit(' ', 1)[0] + "... and I've logged the full details for your review, Sir."
            print(f"JACK Speech Refinement: Truncated {original_len} chars to concise verbal summary.")
        # ------------------------

        with self.speech_lock:
            try:
                print(f"JACK Speaking: {text}")
                try: get_signals().emit_bridge("neural_pulse", 4)
                except: pass
            except UnicodeEncodeError:
                # Fallback for consoles that don't support UTF-8 (like some Windows CMD)
                print(f"JACK Speaking: [Multilingual Content]")

            # Try Premium Voice (Edge-TTS)
            if self.use_premium_voice:
                try:
                    self._speak_premium(text, lang=lang)
                    return
                except Exception as e:
                    print(f"Premium Voice failed: {e}, falling back to offline.")

            # Fallback to Offline Engine
            try:
                self.offline_engine.say(text)
                self.offline_engine.runAndWait()
            except:
                pass

    def _speak_premium(self, text, lang=None):
        """Helper to run async edge-tts in a stable way."""
        try:
            # Resolve Voice
            target_lang = lang or LANGUAGE_SETTINGS["default_lang"]
            voice = LANGUAGE_SETTINGS["voice_map"].get(target_lang, LANGUAGE_SETTINGS["voice_map"]["en"])

            async def _generate():
                communicate = edge_tts.Communicate(text, voice)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp_path = tmp.name
                await communicate.save(tmp_path)
                return tmp_path

            # Generate and play with retry logic
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            path = None
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    path = loop.run_until_complete(_generate())
                    if path: break
                except Exception as e:
                    if attempt == max_retries: raise e
                    print(f"Speech Gen Attempt {attempt+1} failed ({e}), retrying...")
                    time.sleep(1)

            # Play via Pygame (More stable on Windows threads)
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            
            # Wait for playback
            start_wait = time.time()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
                # Safety timeout (30s)
                if time.time() - start_wait > 30:
                    break

            pygame.mixer.music.unload()
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            raise e

    def stop_speaking(self):
        """Stop current speech output."""
        try:
            pygame.mixer.music.stop()
            self.offline_engine.stop()
        except:
            pass
