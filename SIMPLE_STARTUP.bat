@echo off
echo --- J.A.C.K. SIMPLE STARTUP SETUP ---
echo.

set "SCRIPT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_PATH=%SCRIPT_DIR%setup\launch_JACK_silent.vbs"

if not exist "%VBS_PATH%" (
    echo [ERROR] Could not find %VBS_PATH%
    echo Please make sure you are running this from the JACK root folder.
    pause
    exit /b
)

echo [INIT] Adding JACK to your Personal Startup folder...
echo Destination: %STARTUP_FOLDER%

:: Use PowerShell to create a shortcut (.lnk file)
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_FOLDER%\JACK_Startup.lnk'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%SCRIPT_DIR%setup'; $s.Save()"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] JACK is now set to run normally at login.
    echo This did NOT require Admin rights or any special tokens.
    echo.
    echo JACK will launch silently in the background next time you turn on the device.
) else (
    echo [ERROR] Failed to create startup shortcut.
)

pause
