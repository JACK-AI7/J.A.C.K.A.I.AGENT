@echo off
:: Check for administrative privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrative Privileges.
    powershell -ExecutionPolicy Bypass -File "%~dp0IMMORTALIZE_SYSTEM.ps1"
) else (
    echo [INIT] Requesting Administrative Privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)
pause
