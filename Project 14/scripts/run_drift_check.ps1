# PowerShell runtime helper to execute drift healer controller
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

Write-Host "Running GitOps Drift Detection and Reconciliation Engine..." -ForegroundColor Cyan
python drift_healer.py

Pop-Location
