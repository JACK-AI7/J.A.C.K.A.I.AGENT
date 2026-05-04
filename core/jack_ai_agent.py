import re
import os
import time
import traceback
import logging
from speech_handler import SpeechHandler
from ai_handler import AIHandler
from config import RECOGNITION_SETTINGS
from tools import FUNCTION_MAP

# --- PRODUCTION CORE IMPORTS ---
import asyncio
from core.executor import Executor
from core.agent_loop import AgentLoop
from core.tool_router import ToolRouter
from core.state_manager import StateManager
from core.logger import log_event

class JackAIAgent:
    def __init__(self, hud=None, mode="voice"):
        self.mode = mode
        self.hud = hud
        self.speech_handler = None
        self.ai_handler = AIHandler(hud=hud)
        
        # --- PRODUCTION CORE INITIALIZATION ---
        self.state = StateManager()
        self.router = ToolRouter(FUNCTION_MAP)
        self.executor = Executor(self.ai_handler, self.router, self.state)
        self.loop = AgentLoop(self.executor)
        
        # --- GUARDIAN MODE INITIALIZATION ---
        from guardian.guardian_service import GuardianService
        from guardian.scheduler import start_guardian_background
        self.guardian = GuardianService()
        start_guardian_background(self.guardian)
        
        self.is_running = False
        self.is_active = True  # Tracks if AI brain is actually listening
        self.current_language = "en"
        self._consecutive_errors = 0
        self._max_consecutive_errors = 15

    def set_active(self, state):
        """Toggle the AI brain active state."""
        self.is_active = state
        if self.hud:
            status = "Ready" if state else "AI Deactivated"
            self.hud.signals.status_changed.emit(
                status, "idle" if state else "executing"
            )
        print(f"JACK AI Brain: {'ACTIVATED' if state else 'DEACTIVATED'}")

    def start(self):
        """Start JACK and begin listening for commands."""
        print("JACK is starting up...")
        if self.hud:
            self.hud.signals.status_changed.emit("Starting up...", "pulsing")

        # Activate AI brain by default
        self.set_active(True)

        # Initialize speech handler here (in background thread) if in voice mode
        if self.mode == "voice" and not self.speech_handler:
            max_stt_retries = 3
            for attempt in range(max_stt_retries):
                try:
                    from speech_handler import SpeechHandler
                    self.speech_handler = SpeechHandler()
                    print(f"Speech Engine: ONLINE (Attempt {attempt+1})")
                    break
                except Exception as e:
                    print(f"Speech Engine Startup Error (Attempt {attempt+1}/{max_stt_retries}): {e}")
                    if attempt < max_stt_retries - 1:
                        time.sleep(2) # Backoff
                    else:
                        print("Speech Engine: CRITICAL FAILURE - Falling back to Text Mode")
                        self.mode = "text"
                        if self.hud:
                            self.hud.signals.activity_received.emit("System: Speech Engine Failure - Text Mode Active")

        # Complete Calibrate
        try:
            if self.speech_handler:
                self.speech_handler.calibrate_microphone()
        except Exception as e:
            print(f"Calibration warning: {e}")

        self.is_running = True
        self._consecutive_errors = 0
        self._main_loop()

    def stop(self):
        """Stop JACK."""
        self.is_running = False
        if self.hud:
            self.hud.signals.status_changed.emit("Shutting down", "idle")
        try:
            self.speech_handler.speak("Shutting down JACK. Goodbye!")
        except Exception:
            pass
        print("JACK has been shut down.")

    def _main_loop(self):
        """Main loop for processing user input — crash-proof with auto-recovery."""
        while self.is_running:
            try:
                self._main_loop_iteration()
                # Reset error counter on successful iteration
                self._consecutive_errors = 0
            except Exception as e:
                self._consecutive_errors += 1
                error_msg = f"Main loop error #{self._consecutive_errors}: {e}\n{traceback.format_exc()}"
                logging.error(error_msg)
                print(error_msg)
                
                if self._consecutive_errors >= self._max_consecutive_errors:
                    print("SAFE MODE: Too many consecutive errors. Pausing for 30s...")
                    if self.hud:
                        try:
                            self.hud.signals.status_changed.emit("SAFE MODE", "executing")
                        except Exception:
                            pass
                    time.sleep(30)
                    self._consecutive_errors = 0
                    
                    # Try to reinitialize speech handler
                    try:
                        if self.mode == "voice":
                            print("Attempting speech handler recovery...")
                            self.speech_handler = SpeechHandler()
                            self.speech_handler.calibrate_microphone()
                            print("Speech handler recovered!")
                    except Exception as reinit_err:
                        print(f"Speech recovery failed: {reinit_err}")
                        time.sleep(10)
                else:
                    time.sleep(1)  # Brief pause before retry

    def _main_loop_iteration(self):
        """Single iteration of the main loop — can safely raise exceptions."""
        # Check if brain is active
        if not self.is_active:
            if self.hud:
                self.hud.signals.status_changed.emit("AI Deactivated", "executing")
            time.sleep(1)  # Sleep to avoid spinning
            return

        # Listening state
        if self.hud:
            try:
                self.hud.signals.status_changed.emit("Listening...", "listening")
                self.hud.signals.activity_received.emit("System: Listening for commands...")
            except (RuntimeError, AttributeError):
                self.hud = None
        
        try:
            from core.nexus_bridge import get_signals
            get_signals().emit_bridge("pipeline_stage", "LISTENING", "Awaiting voice input...")
            get_signals().emit_bridge("neural_pulse", 2)
        except: pass

        # Listen for speech or get console input
        if self.mode == "voice":
            text = self.speech_handler.listen_for_speech()
        else:
            try:
                text = input("\n[JACK] Awaiting Command Sir: ").strip()
            except EOFError:
                self.stop()
                return

        if not text:
            return

        if self.hud:
            try:
                self.hud.signals.status_changed.emit("Thinking...", "thinking")
                self.hud.signals.activity_received.emit(f"System: Processing query: {text[:50]}...")
                self.hud.signals.transcription_received.emit(text)
            except (RuntimeError, AttributeError):
                self.hud = None
        
        # Dashboard Sync: User Chat + Pipeline
        try:
            from core.nexus_bridge import get_signals
            get_signals().emit_bridge("pipeline_stage", "TRANSCRIBED", f"Heard: {text[:60]}")
            get_signals().emit_bridge("chat_received", "USER", text)
            get_signals().emit_bridge("neural_pulse", 5)
        except: pass

        # Check for stop command
        if text.lower() == "stop":
            self.stop()
            self.is_running = False
            return

        # --- SYSTEM CONTROL BYPASS: shutdown, restart, sleep, lock ---
        text_lower = text.lower().strip()
        system_cmds = {
            'shut down': 'shutdown', 'shutdown': 'shutdown', 'power off': 'shutdown',
            'restart': 'restart', 'reboot': 'restart',
            'sleep': 'sleep', 'hibernate': 'sleep',
            'lock': 'lock', 'lock screen': 'lock',
            'log off': 'log off', 'sign out': 'log off'
        }
        for cmd_phrase, cmd_action in system_cmds.items():
            if cmd_phrase in text_lower:
                try:
                    from tools import system_control
                    result = system_control(cmd_action)
                    self._handle_response(result)
                except Exception as e:
                    self._handle_response(f"System control error: {e}")
                return
        
        # --- WEATHER BYPASS ---
        if any(w in text_lower for w in ['weather', 'temperature', 'forecast', 'how hot', 'how cold']):
            try:
                from tools import get_weather_for_location
                weather = get_weather_for_location()
                self._handle_response(weather)
            except Exception as e:
                self._handle_response(f"Weather check failed: {e}")
            return

        # Check for conversation management commands
        if text.lower() == "clear history":
            response = self.ai_handler.clear_conversation_history()
            self._handle_response(response)
            return

        if text.lower() == "conversation stats":
            stats = self.ai_handler.get_conversation_stats()
            response = f"Stats: {stats['total_interactions']} interactions, {stats['total_tool_calls']} tool calls."
            self._handle_response(response)
            return

        # Clear screen command
        if text.lower() in ("clear screen", "reset display"):
            if self.hud:
                self.hud.signals.status_changed.emit("Screen cleared", "idle")
                self.hud.transcription_label.setText("")
                self.hud.tool_log_label.setText("")
                self.hud.thinking_label.setText("")
                self._handle_response("Screen cleared, Sir.")
            return

        # Language Switching Logic
        if any(cmd in text.lower() for cmd in ["speak in telugu", "switch to telugu"]):
            self.current_language = "te"
            self._handle_response("మీ ఆజ్ఞ ప్రకారం, నేను ఇప్పుడు తెలుగులో మాట్లాడతాను.")
            return
        
        if any(cmd in text.lower() for cmd in ["speak in english", "switch to english", "switch back to english"]):
            self.current_language = "en"
            self._handle_response("Understood, Sir. Switching back to English.")
            return

        if text.lower() in ["minimize", "side rail", "go to rail"]:
            if self.hud:
                self.hud.signals.mini_mode_toggled.emit()
                self._handle_response("Minimizing to Side Rail, Sir.")
            return

        # Process query - More robust wake-word detection
        raw_text = text.lower()
        wake_options = RECOGNITION_SETTINGS.get(
            "wake_words", ["jack", "hey jack", "wakeup"]
        )

        # Sort by length descending to match longest phrases first (e.g., "hey jack" before "jack")
        wake_options = sorted(wake_options, key=len, reverse=True)

        is_wake_word = False
        query = text

        for word in wake_options:
            # Create a regex pattern that ignores injected punctuation between words (e.g., 'hey, jack')
            words = word.split()
            pattern = r'\s*[,\.!?;-]*\s*'.join(re.escape(w) for w in words)
            
            # Use a more aggressive search that handles potential speech-to-text artifacts
            match = re.search(rf"(?:^|\s){pattern}(?:\s|$|[,\.!?;])", query, flags=re.IGNORECASE)
            
            if match:
                is_wake_word = True
                # Safely remove the exact wake phrase from the query
                query = query[:match.start()] + " " + query[match.end():]
                break
                
        query = query.strip(" .,!?\n\t")
        
        # If we have a transcribed query, process it. No strict wake word requirement.
        if query:
            if self.hud and is_wake_word:
                self.hud.signals.restore_requested.emit()
                self.hud.signals.activity_received.emit("System: Wake word detected")

            try:
                from core.nexus_bridge import get_signals
                get_signals().emit_bridge("pipeline_stage", "THINKING", f"Processing: {query[:50]}")
                get_signals().emit_bridge("neural_pulse", 8)
            except: pass
            
            # --- PRODUCTION CORE MISSION EXECUTION ---
            try:
                # Run the autonomous mission loop safely, even if called from an existing event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    import threading
                    result_container = []
                    def _run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result_container.append(new_loop.run_until_complete(self.loop.run(query)))
                        new_loop.close()
                    
                    t = threading.Thread(target=_run_in_thread)
                    t.start()
                    t.join()
                    result = result_container[0]
                else:
                    result = loop.run_until_complete(self.loop.run(query))
                
                # Robust message extraction
                response = result.get("message") or result.get("response") or result.get("answer") or result.get("result")
                if not response:
                    response = "Mission result unavailable."
                
                # Ensure response is a string (might be a dict if LLM returns complex message)
                if not isinstance(response, str):
                    response = str(response)
                    
                self._handle_response(response)
            except Exception as e:
                log_event(f"Mission Loop Failure: {e}")
                self._handle_response(f"I encountered a core error during the mission, Sir: {str(e)}")
            
        elif is_wake_word and not query:
            # Just the wake word (e.g., "Hey Jack") - Acknowledge and restore HUD
            if self.hud:
                self.hud.signals.restore_requested.emit()
                self.hud.signals.status_changed.emit("Standing by", "idle")
                self.hud.signals.activity_received.emit("System: Wake word detected")
            if self.speech_handler:
                self.speech_handler.speak("Yes, Sir?")
            
        else:
            # Empty transcription and no wake word
            return

    def _handle_response(self, response):
        """Helper to handle AI responses consistently."""
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
            
        print(f"JACK: {response}")
        if self.hud:
            try:
                self.hud.signals.response_received.emit(response)
                self.hud.signals.status_changed.emit("Speaking...", "speaking")
                
                # Safe slicing
                display_text = response[:50] if isinstance(response, str) else "Processing..."
                self.hud.signals.activity_received.emit(f"Response: {display_text}...")
            except (RuntimeError, AttributeError):
                self.hud = None
            
        # Dashboard Sync: JACK Chat + Pipeline
        try:
            from core.nexus_bridge import get_signals
            display_text = response[:50] if isinstance(response, str) else "Responding..."
            get_signals().emit_bridge("pipeline_stage", "SPEAKING", f"Responding: {display_text}")
            get_signals().emit_bridge("chat_received", "JACK", response)
            get_signals().emit_bridge("neural_pulse", 4)
        except: pass

        try:
            if self.mode == "voice" and self.speech_handler:
                self.speech_handler.speak(response, lang=self.current_language)
        except Exception as e:
            print(f"Speech output error: {e}")

        if self.hud:
            self.hud.signals.status_changed.emit("Idle", "idle")
            self.hud.signals.activity_received.emit("System: Ready for next command")
        
        try:
            from core.nexus_bridge import get_signals
            get_signals().emit_bridge("pipeline_stage", "IDLE", "Standing by...")
        except: pass

    def process_text_command(self, text):
        """Execute a mission from text input (Production Core Interface)."""
        return asyncio.run(self.loop.run(text))

    def get_conversation_stats(self):
        """Get conversation statistics."""
        return self.ai_handler.get_conversation_stats()

    def clear_history(self):
        """Clear conversation history."""
        return self.ai_handler.clear_conversation_history()
