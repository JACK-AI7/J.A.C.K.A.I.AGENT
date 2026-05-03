import re
import os
import time
import traceback
import logging
from speech_handler import SpeechHandler
from ai_handler import AIHandler
from config import RECOGNITION_SETTINGS


class Jarvis:
    def __init__(self, hud=None):
        self.speech_handler = SpeechHandler()
        self.ai_handler = AIHandler(hud=hud)
        self.is_running = False
        self.is_active = True  # Tracks if AI brain is actually listening
        self.hud = hud
        self.current_language = "en"
        self._consecutive_errors = 0
        self._max_consecutive_errors = 15  # Enter safe mode after this many

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

        # Complete Calibrate
        try:
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
            self.hud.signals.status_changed.emit("Listening...", "listening")
            self.hud.signals.activity_received.emit(
                "System: Listening for commands..."
            )
        
        try:
            from core.nexus_bridge import get_signals
            get_signals().emit_bridge("pipeline_stage", "LISTENING", "Awaiting voice input...")
            get_signals().emit_bridge("neural_pulse", 2)
        except: pass

        # Listen for speech
        text = self.speech_handler.listen_for_speech()

        if not text:
            return

        if self.hud:
            self.hud.signals.status_changed.emit("Thinking...", "thinking")
            self.hud.signals.activity_received.emit(
                f"System: Processing query: {text[:50]}..."
            )
            self.hud.signals.transcription_received.emit(text)
        
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
        if is_wake_word:
            if self.hud:
                self.hud.signals.restore_requested.emit()
                self.hud.signals.status_changed.emit("Listening...", "listening")
                self.hud.signals.activity_received.emit(
                    "System: Wake word detected"
                )

            if query:
                # Direct command with wake word (e.g., "Hey Jack, what time is it?")
                try:
                    from core.nexus_bridge import get_signals
                    get_signals().emit_bridge("pipeline_stage", "THINKING", f"Processing: {query[:50]}")
                    get_signals().emit_bridge("neural_pulse", 8)
                except: pass
                response = self.ai_handler.process_query(query)
                self._handle_response(response)
            else:
                # Just the wake word (e.g., "Hey Jack") - Acknowledge and restore HUD
                if self.hud:
                    self.hud.signals.status_changed.emit("Standing by", "idle")
                self.speech_handler.speak("Yes, Sir?")
        else:
            # Still listening, but didn't detect a command or wake word
            return

    def _handle_response(self, response):
        """Helper to handle AI responses consistently."""
        print(f"JACK: {response}")
        if self.hud:
            self.hud.signals.response_received.emit(response)
            self.hud.signals.status_changed.emit("Speaking...", "speaking")
            self.hud.signals.activity_received.emit(f"Response: {response[:50]}...")
            
        # Dashboard Sync: JACK Chat + Pipeline
        try:
            from core.nexus_bridge import get_signals
            get_signals().emit_bridge("pipeline_stage", "SPEAKING", f"Responding: {response[:50]}")
            get_signals().emit_bridge("chat_received", "JACK", response)
            get_signals().emit_bridge("neural_pulse", 4)
        except: pass

        try:
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

    def get_conversation_stats(self):
        """Get conversation statistics."""
        return self.ai_handler.get_conversation_stats()

    def clear_history(self):
        """Clear conversation history."""
        return self.ai_handler.clear_conversation_history()
