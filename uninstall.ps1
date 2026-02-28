# ============================================================
# ORCHIX - Uninstaller (Windows PowerShell)
# ============================================================

$ErrorActionPreference = "SilentlyContinue"
$BW = 54
$C = "Cyan"; $G = "Green"; $R = "Red"; $W = "White"

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

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

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
        $pid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($pid) { taskkill /PID $pid /F 2>$null | Out-Null }
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
    $removeConfig = Read-Host "  │     Remove config/data at $configDir? [y/N]"
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
$removeDir = Read-Host "  │     Delete $ScriptDir? [y/N]"
if ($removeDir -match '^[Yy]') {
    # Write a temp script and run it after this process exits (reliable for paths with spaces)
    $tmp = [System.IO.Path]::Combine($env:TEMP, "orchix_rm_$(Get-Random).ps1")
    $escaped = $ScriptDir -replace "'", "''"
    "Start-Sleep 3`nRemove-Item -LiteralPath '$escaped' -Recurse -Force -ErrorAction SilentlyContinue`nRemove-Item -LiteralPath `$MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue" | Set-Content $tmp -Encoding UTF8
    Start-Process powershell -ArgumentList "-NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$tmp`"" -WindowStyle Hidden
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
