import os
import threading
import sys
import ctypes
import logging
import time
import traceback
import io
try:
    import win32event
    import win32api
    import winerror
except ImportError:
    win32event = None
    win32api = None
    winerror = None

# --- IO SAFETY: Prevent crashes when stdout/stderr are broken pipes ---
# This happens when launched via VBS silent mode (no console attached)
class SafeWriter:
    """A writer that silently swallows IO errors on broken pipes."""
    def __init__(self, original):
        self._original = original or io.StringIO()
    def write(self, text):
        try:
            self._original.write(text)
        except (OSError, ValueError, AttributeError):
            pass
    def flush(self):
        try:
            self._original.flush()
        except (OSError, ValueError, AttributeError):
            pass
    def fileno(self):
        try:
            return self._original.fileno()
        except (OSError, ValueError, AttributeError, io.UnsupportedOperation):
            return -1

# Ensure stdout/stderr exist (critical for VBS silent launch)
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
# Also fix __stdout__ and __stderr__ for libraries that check them
if sys.__stdout__ is None:
    sys.__stdout__ = sys.stdout
if sys.__stderr__ is None:
    sys.__stderr__ = sys.stderr

sys.stdout = SafeWriter(sys.stdout)
sys.stderr = SafeWriter(sys.stderr)

# --- Force working directory to the script's own folder ---
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# --- Add subdirectories to sys.path for modular imports ---
for folder in ["core", "agents", "gui", "utils", "setup"]:
    folder_path = os.path.join(script_dir, folder)
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)

# Set up logging to file for debugging "just closing" issues
logging.basicConfig(
    filename="jack_error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Global unhandled exception hook — log ALL crashes
def global_exception_hook(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(f"UNHANDLED EXCEPTION:\n{error_msg}")
    try:
        print(f"FATAL UNHANDLED EXCEPTION: {error_msg}")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = global_exception_hook

# --- High DPI & COM Synchronization ---
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTOSCREENSCALEFACTOR"] = "1"

try:
    current_awareness = ctypes.c_int()
    ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(current_awareness))
    if current_awareness.value == 0:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

try:
    ctypes.windll.ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED
except Exception:
    pass

# Global Mutex Handle for Single Instance Check
mutex = None

from core.jack_ai_agent import JackAIAgent
from gui.hud_manager import HUDManager
from core.relay_client import RelayClient


# --- IMMORTAL RESTART CONSTANTS ---
MAX_ASSISTANT_RESTARTS = 999  # TRUE IMMORTALITY — practically infinite
RESTART_COOLDOWN_SECONDS = 3  # Fast recovery


def run_assistant(agent, restart_counter):
    """Entry point for the assistant thread with COM initialization and immortal restart."""
    while restart_counter[0] < MAX_ASSISTANT_RESTARTS:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            
            print(f"Assistant Thread: Starting (attempt {restart_counter[0] + 1})...")
            
            # --- STARTUP GREETING: Speak time-based hello + weather on boot ---
            if restart_counter[0] == 0:  # Only on first boot
                try:
                    import threading
                    def _startup_greeting():
                        import time
                        time.sleep(5)  # Wait for speech engine to initialize
                        try:
                            from tools import get_startup_greeting
                            greeting = get_startup_greeting()
                            print(f"STARTUP GREETING: {greeting}")
                            
                            # Push to dashboard
                            try:
                                from nexus_bridge import get_signals
                                get_signals().emit_bridge("chat_received", "JACK", greeting)
                                get_signals().emit_bridge("pipeline_stage", "SPEAKING", "Startup Greeting")
                            except: pass
                            
                            # Speak the greeting
                            if agent.speech_handler and agent.mode == "voice":
                                agent.speech_handler.speak(greeting)
                            
                            # Also update HUD
                            if agent.hud:
                                agent.hud.signals.response_received.emit(greeting)
                        except Exception as e:
                            print(f"Startup greeting error: {e}")
                    
                    threading.Thread(target=_startup_greeting, daemon=True).start()
                except Exception as e:
                    print(f"Greeting thread error: {e}")
            
            agent.start()
            
            # If start() returns normally (e.g., user said "stop"), exit cleanly
            break
            
        except Exception as e:
            restart_counter[0] += 1
            error_msg = f"Assistant Thread Crash #{restart_counter[0]}: {e}\n{traceback.format_exc()}"
            logging.error(error_msg)
            print(error_msg)
            
            if restart_counter[0] < MAX_ASSISTANT_RESTARTS:
                print(f"IMMORTAL MODE: Auto-restarting in {RESTART_COOLDOWN_SECONDS}s... ({restart_counter[0]}/{MAX_ASSISTANT_RESTARTS})")
                time.sleep(RESTART_COOLDOWN_SECONDS)
                
                # Reset agent state for restart
                agent.is_running = False
                time.sleep(0.5)
            else:
                print("IMMORTAL MODE: Max restarts reached. Assistant entering safe mode.")
                logging.error("IMMORTAL MODE: Max restarts exhausted. Manual intervention required.")
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except:
                pass


def main():
    """Main entry point with global error catching."""
    import argparse
    parser = argparse.ArgumentParser(description="J.A.C.K.A.I.AGENT Core")
    parser.add_argument("--text", action="store_true", help="Run in text-only CLI mode")
    args = parser.parse_args()

    try:
        hud = None
        if not args.text:
            # Initialize HUD
            hud = HUDManager()

        # Initialize J.A.C.K.A.I.AGENT Assistant with HUD reference
        assistant = JackAIAgent(hud=hud, mode="text" if args.text else "voice")
        if hud:
            hud.set_assistant(assistant)

        # Restart counter (mutable list so thread can update it)
        restart_counter = [0]

        # Run assistant in separate thread with immortal restart
        assistant_thread = threading.Thread(
            target=run_assistant, args=(assistant, restart_counter), daemon=True
        )
        assistant_thread.start()

        # --- START NEURAL RELAY (Mobile Bridge) ---
        def _start_relay():
            try:
                import subprocess
                import socket
                
                # Get Local IP for user reference
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    print(f"\n[NETWORK] MOBILE_LINK_IP: {local_ip}:8001")
                    if hud:
                        hud.signals.activity_received.emit(f"Mobile Link: {local_ip}:8001")
                except:
                    print("\n[NETWORK] Local IP detection failed. Check your router settings.")

                relay_script = os.path.join(script_dir, "api", "relay_server.py")
                # Run in separate process to avoid blocking
                subprocess.Popen([sys.executable, relay_script], 
                               cwd=script_dir,
                               creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
                print("TITAN RELAY: Online (Port 8001)")
                
                # Wait for relay to boot, then connect bridge
                time.sleep(2)
                bridge = RelayClient(assistant)
                bridge.start()
                
            except Exception as e:
                print(f"TITAN RELAY Error: {e}")
        
        threading.Thread(target=_start_relay, daemon=True).start()

        if not args.text:
            # Show HUD and run its event loop (main thread)
            print("Launching J.A.C.K.A.I.AGENT Core Interface...")
            hud.show()
        else:
            print("J.A.C.K.A.I.AGENT running in TEXT MODE.")


        # Graceful Shutdown
        def shutdown():
            print("\nShutting down J.A.C.K.A.I.AGENT Core...")
            try:
                assistant.stop()
            except Exception:
                pass
            time.sleep(0.5)
            if mutex:
                try:
                    win32api.CloseHandle(mutex)
                except Exception:
                    pass

        if hud and hasattr(hud, 'app') and hud.app:
            try:
                hud.app.aboutToQuit.connect(shutdown)
            except Exception: pass
        print("TITAN_SYSTEM: ONLINE")
        
        # Dashboard Lively Feed
        try:
            from nexus_bridge import get_signals
            signals = get_signals()
            signals.emit_bridge("pipeline_stage", "INITIALIZED", "TITAN SYSTEM ONLINE")
            signals.emit_bridge("neural_pulse", 20)
        except: pass

        # Run the event loop
        if hud:
            # GUI Mode: Run the Qt event loop
            try:
                if hud.app:
                    return hud.app.exec()
                else:
                    print("HUD Error: Application instance missing. Falling back to CLI behavior.")
                    # Fall through to CLI logic
            except (SystemExit, AttributeError):
                shutdown()
                return 0
        else:
            # CLI Mode: Keep the main thread alive while the assistant thread is running
            print("JACK CLI: System fully operational. Press Ctrl+C to shutdown.")
            try:
                while assistant_thread.is_alive():
                    assistant_thread.join(timeout=1.0)
            except KeyboardInterrupt:
                shutdown()
            return 0

    except Exception as e:
        error_msg = f"FATAL Startup Error: {e}\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(f"FATAL ERROR: {error_msg}")
        print("See jack_error.log for details.")
        if mutex:
            try:
                win32api.CloseHandle(mutex)
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    # Single Instance Check using Windows Mutex
    if win32event and win32api and winerror:
        try:
            mutex_name = "JACK_Single_Instance_Mutex_V2"
            mutex = win32event.CreateMutex(None, False, mutex_name)
            last_error = win32api.GetLastError()
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                print("JACK is already running. Shifting focus to existing instance.")
                win32api.CloseHandle(mutex)
                sys.exit(1)
        except Exception as e:
            print(f"Single-instance check failed: {e}")
    else:
        print("Single-instance check unavailable: win32 libraries missing.")

    sys.exit(main())
