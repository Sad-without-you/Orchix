# ============================================================
# ORCHIX - Uninstaller (Windows PowerShell)
# ============================================================

$ErrorActionPreference = "SilentlyContinue"
$BW = 54
$C = "Cyan"; $G = "Green"; $W = "White"

function Write-BoxLine($text, $color = "Cyan") {
    Write-Host ("  ║" + $text.PadRight($BW) + "║") -ForegroundColor $color
}
function Write-BoxTop($color = "Cyan") {
    Write-Host ("  ╔" + ("═" * $BW) + "╗") -ForegroundColor $color
}
function Write-BoxBottom($color = "Cyan") {
    Write-Host ("  ╚" + ("═" * $BW) + "╝") -ForegroundColor $color
}
function Write-Step($msg) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  ├─ " -NoNewline -ForegroundColor $C
    Write-Host $msg -ForegroundColor $W
}
function Write-StepOK($msg) {
    Write-Host "  │  " -NoNewline -ForegroundColor $C
    Write-Host "OK " -NoNewline -ForegroundColor $G
    Write-Host $msg -ForegroundColor DarkGreen
}
function Write-StepFinal($msg) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  └─ " -NoNewline -ForegroundColor $C
    Write-Host "OK " -NoNewline -ForegroundColor $G
    Write-Host $msg -ForegroundColor DarkGreen
}

$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $PSCommandPath }
if (-not $ScriptDir -and $MyInvocation.MyCommand.Path) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = $PWD.Path }

Clear-Host
Write-Host ""
Write-BoxTop "Red"
Write-BoxLine ""
Write-BoxLine "   ___  ____   ____ _   _ _____  __"
Write-BoxLine "  / _ \|  _ \ / ___| | | |_ _\ \/ /"
Write-BoxLine " | | | | |_) | |   | |_| || | \  / "
Write-BoxLine " | |_| |  _ <| |___|  _  || | /  \ "
Write-BoxLine "  \___/|_| \_\____|_| |_|___/_/\_\"
Write-BoxLine ""
Write-BoxLine "   Uninstall"
Write-BoxLine ""
Write-BoxBottom "Red"
Write-Host ""

# ── 1. Stop and remove service ────────────────────────────────────────────────
Write-Step "Stopping ORCHIX Web UI service..."
$pythonVenv = "$ScriptDir\.venv\Scripts\python.exe"
if (Test-Path $pythonVenv) {
    & $pythonVenv "$ScriptDir\main.py" service uninstall 2>$null
} else {
    # Fallback: manual cleanup
    # Remove registry autostart entry (no admin needed)
    Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "ORCHIX-WebUI" -ErrorAction SilentlyContinue
    $pidFile = "$env:USERPROFILE\.orchix_configs\orchix.pid"
    if (Test-Path $pidFile) {
        $orchixPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($orchixPid) { Stop-Process -Id ([int]$orchixPid) -Force -ErrorAction SilentlyContinue }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}
Write-StepOK "Service stopped and removed"

# ── 2. Remove from PATH ───────────────────────────────────────────────────────
Write-Step "Removing from PATH..."
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$ScriptDir*") {
    $newPath = ($userPath -split ';' | Where-Object { $_ -ne $ScriptDir }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-StepOK "Removed from PATH"
} else {
    Write-StepOK "Not in PATH"
}

# ── 3. Ask about config data ──────────────────────────────────────────────────
Write-Step "Config & data files..."
$configDir = "$env:USERPROFILE\.orchix_configs"
if (Test-Path $configDir) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  │     Remove config/data at '$configDir'? [y/N] " -NoNewline -ForegroundColor $W
    $removeConfig = Read-Host
    if ($removeConfig -match '^[Yy]') {
        Remove-Item $configDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-StepOK "Config directory removed"
    } else {
        Write-StepOK "Config directory kept"
    }
} else {
    Write-StepOK "No config directory found"
}

# ── 4. Remove ORCHIX directory ────────────────────────────────────────────────
Write-Step "Removing ORCHIX installation..."
Write-Host "  │" -ForegroundColor $C
Write-Host "  │     Delete '$ScriptDir'? [y/N] " -NoNewline -ForegroundColor $W
$removeDir = Read-Host
if ($removeDir -match '^[Yy]') {
    # Move out of the ORCHIX folder first — otherwise Windows locks the root dir (CWD)
    Set-Location $env:TEMP
    Start-Process cmd -ArgumentList "/c timeout /t 2 /nobreak >NUL & rd /s /q `"$ScriptDir`"" -WindowStyle Hidden
    Write-StepFinal "ORCHIX will be removed in a moment"
} else {
    Write-StepFinal "Skipped (directory kept)"
}

Write-Host ""
Write-BoxTop "Green"
Write-BoxLine "" "Green"
Write-BoxLine "   ORCHIX uninstalled successfully" "Green"
Write-BoxLine "" "Green"
Write-BoxBottom "Green"
Write-Host ""
Read-Host "  Press Enter to exit"
