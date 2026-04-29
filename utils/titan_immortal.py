import subprocess
import time
import sys
import os
import datetime

# --- CONFIGURATION ---
TARGET_SCRIPT = "main.py"
RESTART_DELAY = 3  # seconds to wait before rebirth (faster recovery)
LOG_FILE = "immortal.log"
CRASH_LOG = "jack_error.log"
MAX_RAPID_CRASHES = 5  # Throttle if crashing too fast
RAPID_CRASH_WINDOW = 30  # seconds

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception:
        pass

def run_jack():
    """Launch JACK with TRUE IMMORTAL mode — never dies, always recovers."""
    log_event("IMMORTAL CORE: Initializing TITAN Pulse... TRUE IMMORTALITY ENGAGED.")
    
    # Get current python executable
    python_exe = sys.executable
    crash_times = []  # Track rapid crash detection
    total_restarts = 0
    
    while True:
        try:
            total_restarts += 1
            log_event(f"IMMORTAL CORE: Launching {TARGET_SCRIPT} (Revival #{total_restarts})...")
            
            # Start the main process
            process = subprocess.run([python_exe, TARGET_SCRIPT], capture_output=False)
            
            # If it exits with 0, user closed it normally (via exit command)
            if process.returncode == 0:
                log_event("IMMORTAL CORE: JACK terminated gracefully by User. Shuttering Titan.")
                break
            else:
                crash_time = time.time()
                crash_times.append(crash_time)
                
                # Clean old crash times (outside the rapid window)
                crash_times = [t for t in crash_times if crash_time - t < RAPID_CRASH_WINDOW]
                
                log_event(f"IMMORTAL CORE: !! CRITICAL FAILURE !! JACK exited with code {process.returncode}")
                
                # Check crash log for highlights
                if os.path.exists(CRASH_LOG):
                    try:
                        with open(CRASH_LOG, "r") as f:
                            lines = f.readlines()
                            if lines:
                                last_error = lines[-1].strip()
                                log_event(f"LAST TRACE: {last_error}")
                    except Exception:
                        pass
                
                # Rapid crash throttling
                if len(crash_times) >= MAX_RAPID_CRASHES:
                    throttle_delay = 30
                    log_event(f"IMMORTAL CORE: Rapid crash detected ({len(crash_times)} in {RAPID_CRASH_WINDOW}s). Throttling for {throttle_delay}s...")
                    time.sleep(throttle_delay)
                    crash_times.clear()
                else:
                    log_event(f"IMMORTAL CORE: Initiating Rebirth in {RESTART_DELAY}s... (Total revivals: {total_restarts})")
                    time.sleep(RESTART_DELAY)
                
        except KeyboardInterrupt:
            log_event("IMMORTAL CORE: Manual shutdown detected. Dispersing.")
            break
        except Exception as e:
            log_event(f"IMMORTAL CORE: Watchdog Error: {str(e)}")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    # FIXED: Navigate to the PROJECT ROOT (parent of utils/), not the script's own directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up from utils/ to jarvis-main/
    os.chdir(project_root)
    log_event(f"IMMORTAL CORE: Working directory set to {project_root}")
    run_jack()
