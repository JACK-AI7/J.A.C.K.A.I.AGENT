@echo off
echo ==========================================
echo      J.A.C.K. TITAN - IMMORTAL START
echo ==========================================
echo.
cd /d "%~dp0.."

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated.
) else (
    echo [WARNING] No venv found. Using system Python.
    echo          Run INSTALL_JACK.bat first for best results.
)

:: Auto-start Ollama in background if not running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if %errorlevel% neq 0 (
    echo [INIT] Starting Ollama Neural Engine...
    start /B ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo [INIT] Launching J.A.R.V.I.S. Immortal Core (Watchdog)...
echo.
python main.py
echo.

:: If python exits with error, show the log
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] JACK crashed. Checking error log...
    if exist "jack_error.log" (
        echo --- Last 10 lines of jack_error.log ---
        powershell -Command "Get-Content jack_error.log -Tail 10"
    )
)

echo.
echo Process terminated.
pause
