import subprocess
import time
import sys
import os
import datetime

# --- CONFIGURATION ---
TARGET_SCRIPT = "main.py"
RESTART_DELAY = 5 # seconds to wait before rebirth
LOG_FILE = "immortal.log"
CRASH_LOG = "jack_error.log"

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def run_jack():
    """Launch JACK and monitor the process."""
    log_event("IMMORTAL CORE: Initializing TITAN Pulse...")
    
    # Get current python executable
    python_exe = sys.executable
    
    while True:
        try:
            log_event(f"IMMORTAL CORE: Launching {TARGET_SCRIPT}...")
            
            # Start the main process
            # We use subprocess.run so we wait for it to exit
            process = subprocess.run([python_exe, TARGET_SCRIPT], capture_output=False)
            
            # If it exits with 0, user closed it normally (via exit command)
            if process.returncode == 0:
                log_event("IMMORTAL CORE: JACK terminated gracefully by User. Shuttering Titan.")
                break
            else:
                log_event(f"IMMORTAL CORE: !! CRITICAL FAILURE !! JACK exited with code {process.returncode}")
                
                # Check crash log for highlights
                if os.path.exists(CRASH_LOG):
                    with open(CRASH_LOG, "r") as f:
                        last_error = f.readlines()[-1:]
                        if last_error:
                            log_event(f"LAST TRACE: {last_error[0].strip()}")
                
                log_event(f"IMMORTAL CORE: Initiating Rebirth in {RESTART_DELAY}s...")
                time.sleep(RESTART_DELAY)
                
        except KeyboardInterrupt:
            log_event("IMMORTAL CORE: Manual shutdown detected. Dispersing.")
            break
        except Exception as e:
            log_event(f"IMMORTAL CORE: Watchdog Error: {str(e)}")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    # Ensure we are in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_jack()
