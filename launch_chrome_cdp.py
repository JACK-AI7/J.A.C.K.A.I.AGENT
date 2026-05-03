#!/usr/bin/env python
"""Launch Chrome with remote debugging for CDP attachment."""
import subprocess
import time
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
debug_port = 9222

# Launch Chrome with remote debugging
cmd = [
    chrome_path,
    f"--remote-debugging-port={debug_port}",
    f"--user-data-dir={user_data_dir}",
    "--no-first-run",
    "--disable-default-apps",
    "https://www.youtube.com"  # start at YouTube
]

print(f"Launching Chrome with CDP on port {debug_port}...")
print("This opens a new Chrome window that the agent can attach to.")
print("Press Enter to continue or Ctrl+C to cancel...")
input()

try:
    proc = subprocess.Popen(cmd)
    print(f"Chrome started (PID {proc.pid})")
    print("You can now run the Enhanced BrowserOnlyAgent with use_existing_chrome=True")
    print("It will attach to this window via CDP.")
    print("\nKeep this window open. Press Ctrl+C to stop Chrome when done.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Chrome...")
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()
    print("Chrome closed")
