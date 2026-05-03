#!/usr/bin/env python
"""Quick test: Open YouTube in Chrome, inspect UIA tree to see if video elements are accessible"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import time
from pywinauto import Desktop
from pywinauto.application import Application

print("="*60)
print("YOUTUBE UIA INSPECTION TEST")
print("="*60)

# Launch Chrome to YouTube
print("\n[1] Launching Chrome to YouTube...")
import subprocess
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
url = "https://www.youtube.com"
subprocess.Popen([chrome_path, url])
print(f"  Started: {chrome_path}")
print("  Waiting 5 seconds for page load...")
time.sleep(5)

# Find Chrome window
print("\n[2] Finding Chrome window via UIA...")
desktop = Desktop(backend="uia")
chrome_wins = [w for w in desktop.windows() if "Chrome" in w.window_text()]
if not chrome_wins:
    print("  ERROR: No Chrome window found")
    sys.exit(1)
chrome_win = chrome_wins[0]
print(f"  Found window: '{chrome_win.window_text()}' (PID: {chrome_win.process_id})")

# Focus it
try:
    chrome_win.set_focus()
    time.sleep(1)
except Exception as e:
    print(f"  set_focus warning: {e}")

# Capture UIA tree
print("\n[3] Scanning UIA descendants (first 50)...")
desc = list(chrome_win.descendants())
print(f"  Total descendants: {len(desc)}")
print("\n  First 20 elements:")
for i, el in enumerate(desc[:20]):
    info = el.element_info
    print(f"  [{i:02d}] {info.control_type:<20} name='{info.name[:60]}'  class='{info.class_name}'  auto_id='{info.automation_id}'")

# Try to find video-related elements
print("\n[4] Searching for video elements...")
# Common patterns: YouTube uses links for video titles, often with role=link or button
video_candidates = []
for el in desc:
    info = el.element_info
    # Look for clickable elements with non-empty name not obviously chrome UI
    if info.control_type in ("Hyperlink", "Button", "ListItem") and info.name:
        # Filter out chrome's own UI (address bar, tabs)
        if any(skip in info.name.lower() for skip in ["address", "search", "new tab", "bookmarks", "settings", "minimize", "maximize", "close"]):
            continue
        video_candidates.append(el)

print(f"  Found {len(video_candidates)} potential video elements:")
for el in video_candidates[:10]:
    print(f"    - {el.element_info.control_type}: '{el.element_info.name[:80]}'")

# Try clicking the first candidate that looks like a video title (often contains numbers or duration)
target = None
for el in video_candidates:
    name = el.element_info.name
    # Heuristic: video titles often have duration in format "12:34" or include many words
    if ":" in name or len(name) > 20:
        target = el
        break
if not target and video_candidates:
    target = video_candidates[0]

if target:
    print(f"\n[5] Clicking element: '{target.element_info.name[:80]}'")
    try:
        target.click_input()
        print("  Click succeeded")
    except Exception as e:
        print(f"  Click failed: {e}")
else:
    print("  No suitable video element found to click")

print("\n" + "="*60)
print("Inspection done. Check above for element names.")
print("="*60)
