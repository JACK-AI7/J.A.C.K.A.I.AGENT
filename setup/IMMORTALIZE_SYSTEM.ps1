# J.A.C.K. TITAN: IMMORTALIZE SYSTEM (STARTUP INTEGRATION)
# This script registers JACK as a startup job in Windows Task Scheduler.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BatchFile = Join-Path $ScriptDir "START_JACK.bat"
$VbsFile = Join-Path $ScriptDir "launch_JACK_silent.vbs"
$TaskName = "JACK_TITAN_IMMORTAL"

# Check for Admin Privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "--- ERROR: ADMINISTRATIVE PRIVILEGES REQUIRED ---" -ForegroundColor Red
    Write-Host "Please run this script (or your terminal) as Administrator to register the startup task." -ForegroundColor Yellow
    exit 1
}

Write-Host "--- TITAN IMMORTALIZER: Syncing with Windows Services ---" -ForegroundColor Cyan

# Check if Task already exists and remove it to update
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "[INIT] Updating existing Titan Task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Define the Action: Run the Silent VBS Launcher
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsFile`"" -WorkingDirectory $ScriptDir

# Define the Trigger: At Log On of the current user
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Define the Settings: Priority, Power, etc.
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Register the Task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "J.A.C.K. TITAN Immortal Orchestrator (Auto-Restart & HUD)" -RunLevel Highest -ErrorAction Stop
    Write-Host "SUCCESS: JACK is now ingrained into the system fabric." -ForegroundColor Green
    Write-Host "Location: $TaskName will trigger at next Login." -ForegroundColor Gray
} catch {
    Write-Host "CRITICAL FAILURE: Could not register scheduled task." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor White
    exit 1
}
