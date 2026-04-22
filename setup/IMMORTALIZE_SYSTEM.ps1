# J.A.C.K. TITAN: IMMORTALIZE SYSTEM (STARTUP INTEGRATION)
# This script registers JACK as a startup job in Windows Task Scheduler.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BatchFile = Join-Path $ScriptDir "START_JACK.bat"
$VbsFile = Join-Path $ScriptDir "launch_JACK_silent.vbs"
$TaskName = "JACK_TITAN_IMMORTAL"

Write-Host "--- TITAN IMMORTALIZER: Syncing with Windows Services ---" -ForegroundColor Cyan

# Check if Task already exists and remove it to update
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "[INIT] Updating existing Titan Task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Define the Action: Run the Silent VBS Launcher
# We use wscript.exe to run the VBScript
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsFile`"" -WorkingDirectory $ScriptDir

# Define the Trigger: At Log On of the current user
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Define the Settings: Priority, Power, etc.
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Register the Task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "J.A.C.K. TITAN Immortal Orchestrator (Auto-Restart & HUD)" -RunLevel Highest

Write-Host "SUCCESS: JACK is now ingrained into the system fabric." -ForegroundColor Green
Write-Host "Location: $TaskName will trigger at next Login." -ForegroundColor Gray
