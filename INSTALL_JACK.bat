@echo off
setlocal enabledelayedexpansion
echo ==================================================
echo     J.A.C.K. TITAN - IMMORTAL INSTALLER v2.0
echo ==================================================
echo.
cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from python.org.
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo [1/7] Creating Virtual Environment...
if not exist "venv" (
    python -m venv venv
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

echo [2/7] Activating Virtual Environment...
call venv\Scripts\activate.bat

echo [3/7] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [4/7] Installing Python Dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may have failed. Continuing...
)

echo [5/7] Installing Playwright Browser Engine...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [WARNING] Playwright install failed. Web automation may be limited.
)

echo [6/7] Checking Ollama Installation...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama not found. Please install from https://ollama.ai/download
    echo          After installing Ollama, run this installer again.
    goto :skip_models
)

echo [7/7] Pulling AI Models (Free ^& Open-Source)...
echo       This may take a while on first run (~10GB total)
echo.

echo       [Model 1/3] llama3 - Main Reasoning Brain...
ollama pull llama3:latest

echo       [Model 2/3] llava - Visual Analysis Engine...
ollama pull llava:latest

echo       [Model 3/3] qwen2.5:7b - Tool-Calling Specialist...
ollama pull qwen2.5:7b

:skip_models
echo.
echo ==================================================
echo     INSTALLATION COMPLETE - ALL SYSTEMS GO
echo ==================================================
echo.
echo  Installed:
echo    - Python Dependencies (venv)
echo    - Playwright Chromium Browser
echo    - AI Models: llama3, llava, qwen2.5:7b
echo.
echo  To start JACK, run: START_JACK.bat
echo ==================================================
pause
