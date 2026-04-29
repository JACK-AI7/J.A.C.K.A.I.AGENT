@echo off
REM JACK AI - Production Core Installer (Windows)
REM (C) 2026 B. Jaswanth Reddy

echo 🚀 Initializing TITAN Installation Grid...

REM 1. Core Dependencies
echo 📦 Installing Python dependencies...
pip install -r setup/requirements_production.txt

REM 2. Neural Models (Ollama)
echo 🧠 Synchronizing Neural Models via Ollama...
where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    ollama pull qwen2.5-coder:7b
    ollama pull mistral:latest
) else (
    echo ❌ ERROR: Ollama not found. Please install Ollama from https://ollama.com first.
    pause
    exit /b 1
)

REM 3. Vision & Web Drivers
echo 🌐 Initializing Web & Vision Drivers...
playwright install chromium

REM 4. Vault Initialization
echo 🔒 Initializing Neural Vault...
if not exist vault\memory mkdir vault\memory
if not exist logs mkdir logs

echo ✅ JACK is ready for Overdrive. Run 'python api/server.py' to begin mission orchestration.
pause
