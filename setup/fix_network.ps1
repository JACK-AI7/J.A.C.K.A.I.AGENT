# J.A.C.K. TITAN: NETWORK REPAIR SCRIPT
# This script opens port 8001 in the Windows Firewall for Mobile connectivity.

$Port = 8001
$RuleName = "JACK_RELAY_INBOUND"

Write-Host "--- TITAN NETWORK REPAIR: Adjusting Firewall Fabric ---" -ForegroundColor Cyan

# Check if Rule exists
$existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "[INIT] Rule '$RuleName' already exists. Re-initializing..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $RuleName
}

try {
    New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -Description "Allow J.A.C.K. Mobile Relay Connectivity" -ErrorAction Stop
    Write-Host "SUCCESS: Port $Port is now open for Neural Link." -ForegroundColor Green
} catch {
    Write-Host "CRITICAL FAILURE: Could not modify firewall rules." -ForegroundColor Red
    Write-Host "Please ensure you are running as Administrator." -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor White
}
