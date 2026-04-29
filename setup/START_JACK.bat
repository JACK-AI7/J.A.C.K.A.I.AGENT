@echo off
setlocal
echo ==========================================
echo      J.A.C.K. TITAN - IMMORTAL START
echo ==========================================
echo.

:: Get the root directory (one level up from setup folder)
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Neural Workspace Activated.
) else (
    echo [WARNING] No venv found. Using system Python.
    echo          Run install.bat first for best results.
)

:: Auto-start Ollama in background if not running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if %errorlevel% neq 0 (
    echo [INIT] Starting Ollama Neural Engine...
    start /B ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo [INIT] Launching J.A.R.V.I.S. Immortal Core...
echo.

:: Run main.py
python main.py

:: If python exits with error, show the log
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] JACK encountered a core failure. Checking error log...
    if exist "jack_error.log" (
        echo --- Last 10 lines of jack_error.log ---
        powershell -Command "Get-Content jack_error.log -Tail 10"
    )
)

echo.
echo System session terminated.
pause
