param(
    [switch]$NoBot = $false
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path (Join-Path (Join-Path $root ".venv") "Scripts") "python.exe"
$zapretDir = Join-Path $root "zapret"

Write-Host "=== School Manager ===" -ForegroundColor Cyan

# Check .env
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "WARNING: .env not found. Copy .env.example to .env and set TELEGRAM_BOT_TOKEN." -ForegroundColor Yellow
}

# Zapret check
$zapretRunning = Get-Process -Name "winws" -ErrorAction SilentlyContinue
if (-not $zapretRunning) {
    Write-Host "WARNING: zapret (winws.exe) is NOT running." -ForegroundColor Yellow
    Write-Host "  If Telegram is blocked, run as Administrator: $zapretDir\run_telegram.cmd" -ForegroundColor Yellow
    Write-Host ""
}

# Check/create venv
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $root ".venv")
}

# Install deps
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install -q -r (Join-Path $root "backend\requirements.txt") 2>$null
& $venvPython -m pip install -q -r (Join-Path $root "bot\requirements.txt") 2>$null

# Start Django
Write-Host ""
Write-Host "Starting Django on http://localhost:8000 ..." -ForegroundColor Green
$djangoDir = Join-Path $root "backend"

$djangoProcess = Start-Process -FilePath $venvPython `
    -ArgumentList "manage.py runserver 0.0.0.0:8000" `
    -WorkingDirectory $djangoDir `
    -PassThru -NoNewWindow

# Start Bot
if (-not $NoBot) {
    Write-Host "Starting Telegram bot ..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    $botProcess = Start-Process -FilePath $venvPython `
        -ArgumentList "bot\bot.py" `
        -WorkingDirectory $root `
        -PassThru -NoNewWindow
}

Write-Host ""
Write-Host "=== Services ===" -ForegroundColor Cyan
Write-Host "  Web:    http://localhost:8000" -ForegroundColor White
Write-Host "  Admin:  http://localhost:8000/admin/" -ForegroundColor White
Write-Host "  API:    http://localhost:8000/api/" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

try {
    $djangoProcess.WaitForExit()
}
finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    if ($djangoProcess -and !$djangoProcess.HasExited) { $djangoProcess.Kill() }
    if (-not $NoBot -and $botProcess -and !$botProcess.HasExited) { $botProcess.Kill() }
    Write-Host "Done." -ForegroundColor Green
}
