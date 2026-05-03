#!/usr/bin/env python
"""Detect installed applications on Windows system"""
import subprocess
import os
import sys

def run_ps(cmd):
    result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

print("="*60)
print("INSTALLED APPS SCAN")
print("="*60)

# 1. Check for YouTube (Store app, Chrome, Edge)
print("\n[1] Checking for YouTube...")
stdout, stderr, code = run_ps("Get-StartApps | Where-Object {$_.Name -like '*YouTube*'} | Select-Object Name, AppID")
if stdout:
    print("  Found YouTube Start Menu apps:")
    print("  ", stdout.replace('\n', '\n    '))
else:
    print("  No YouTube start menu app found")

# Check for YouTube.exe in common locations
paths = [
    os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WindowsApps\yt.exe'),
    os.path.expandvars(r'%ProgramFiles%\YouTube\YouTube.exe'),
    os.path.expandvars(r'%ProgramFiles(x86)%\YouTube\YouTube.exe'),
]
for p in paths:
    if os.path.exists(p):
        print(f"  Found YouTube at: {p}")
else:
    print("  No YouTube.exe found")

# 2. Check browsers
print("\n[2] Checking browsers...")
browsers = {
    "Chrome": r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    "Chrome (x86)": r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    "Edge": r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    "Firefox": r"%ProgramFiles%\Mozilla Firefox\firefox.exe",
}
for name, path in browsers.items():
    expanded = os.path.expandvars(path)
    if os.path.exists(expanded):
        print(f"  [OK] {name}: {expanded}")
    else:
        print(f"  [MISSING] {name}: {expanded}")

# 3. Check if pywinauto can get UIA tree
print("\n[3] Testing pywinauto UIA...")
try:
    from pywinauto import Desktop
    desktop = Desktop(backend="uia")
    windows = desktop.windows()
    print(f"  pywinauto UIA OK - {len(windows)} top-level windows")
    # Show active window
    try:
        active = windows[0]
        print(f"  Top window: '{active.window_text()}' (PID: {active.process_id})")
    except Exception as e:
        print(f"  Could not get top window: {e}")
except Exception as e:
    print(f"  pywinauto error: {e}")

print("\n" + "="*60)
print("SCAN COMPLETE")
print("="*60)
