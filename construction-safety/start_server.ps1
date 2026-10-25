<#
.SYNOPSIS
    Starts SiteGuard Safety Monitoring Server
#>
$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$server = Join-Path $PSScriptRoot "server.py"

Write-Host "Starting SiteGuard Safety Server..." -ForegroundColor Cyan
& $python $server
