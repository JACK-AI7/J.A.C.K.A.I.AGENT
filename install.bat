@echo off
setlocal enabledelayedexpansion
echo ==================================================
echo     J.A.C.K. TITAN - ONE-CLICK INSTALLER
echo ==================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from python.org.
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: 2. Create Virtual Environment
echo [1/6] Initializing Neural Workspace (venv)...
if not exist "venv" (
    python -m venv venv
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

:: 3. Upgrade Pip
echo [2/6] Optimizing Pip Pipeline...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

:: 4. Install Dependencies
echo [3/6] Synchronizing Dependencies...
echo       This may take a moment (Installing PySide6, Torch, RealtimeSTT/TTS)...
pip install -r setup/requirements_production.txt
if %errorlevel% neq 0 (
    echo [WARNING] Dependency synchronization encountered issues. Continuing...
)

:: 5. Pull Models
echo [4/6] Connecting to Neural Hub (Ollama)...
where ollama >nul 2>nul
if %errorlevel% equ 0 (
    echo       Pulling Models (llama3, qwen2.5:7b, llava)...
    ollama pull llama3:latest
    ollama pull qwen2.5:7b
    ollama pull llava:latest
) else (
    echo [WARNING] Ollama not detected. Please install it from https://ollama.ai/
)

:: 6. Install Playwright
echo [5/6] Calibrating Visual Sensors (Playwright)...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [WARNING] Visual sensor calibration failed.
)

:: 7. Finalize
echo [6/6] Finalizing System Initialization...
if not exist "vault\memory" mkdir "vault\memory"
if not exist "logs" mkdir "logs"

echo.
echo ==================================================
echo     INSTALLATION COMPLETE - ALL SYSTEMS GO
echo ==================================================
echo.
echo  To launch JACK, run: START_JACK.bat (in root or setup folder)
echo  Or run: SIMPLE_STARTUP.bat to enable auto-start.
echo.
pause
