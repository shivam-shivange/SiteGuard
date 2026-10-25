<#
.SYNOPSIS
    Automated compile and flash script for SiteGuard ESP32-CAM firmware.
#>
param(
    [string]$Port = "COM7"
)

$arduinoCli = "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
$sketchPath = $PSScriptRoot
$fqbn = "esp32:esp32:esp32cam"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SiteGuard ESP32-CAM Firmware Flasher" -ForegroundColor Cyan
Write-Host " Port: $Port | FQBN: $fqbn" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $arduinoCli)) {
    Write-Error "arduino-cli.exe not found at $arduinoCli"
    exit 1
}

Write-Host "`n[1/2] Compiling firmware..." -ForegroundColor Yellow
& $arduinoCli compile --fqbn $fqbn $sketchPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Compilation failed."
    exit $LASTEXITCODE
}

Write-Host "`n[2/2] Uploading firmware to $Port..." -ForegroundColor Yellow
& $arduinoCli upload -p $Port --fqbn $fqbn $sketchPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] Upload failed. If using an FTDI adapter without auto-reset, connect GPIO 0 to GND and press RST, then retry." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[+] Firmware flashed successfully to $Port!" -ForegroundColor Green
