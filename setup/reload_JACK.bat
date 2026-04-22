@echo off
echo --- JACK TITAN: HOT RELOAD INITIATED ---
echo 1. Terminating existing AI processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
echo 2. Clearing UI artifacts...
echo 3. Launching Immortal TITAN Core (New UI)...
start python main.py
echo --- RELOAD COMPLETE: Watch your screen's left edge! ---
pause
