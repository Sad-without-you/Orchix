# ============================================================
# ORCHIX v1.4 - Windows PowerShell Installer
# ============================================================
# Run with: irm https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.ps1 | iex
# ============================================================

$ErrorActionPreference = "Stop"
$ORCHIX_VERSION = "v1.4"
$GITHUB_ZIP = "https://github.com/Sad-without-you/Orchix/archive/refs/heads/main.zip"
$BW = 54  # box inner width

$C = "Cyan"; $G = "Green"; $W = "White"; $R = "Red"; $Y = "Yellow"

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
function Write-Fail($msg) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  └─ " -NoNewline -ForegroundColor $C
    Write-Host "ERROR: $msg" -ForegroundColor $R
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

# ── Banner ───────────────────────────────────────────────────
Clear-Host
Write-Host ""
Write-BoxTop
Write-BoxLine ""
Write-BoxLine "   ___  ____   ____ _   _ _____  __"
Write-BoxLine "  / _ \|  _ \ / ___| | | |_ _\ \/ /"
Write-BoxLine " | | | | |_) | |   | |_| || | \  / "
Write-BoxLine " | |_| |  _ <| |___|  _  || | /  \ "
Write-BoxLine "  \___/|_| \_\\____|_| |_|___/_/\_\"
Write-BoxLine ""
Write-BoxLine "   $ORCHIX_VERSION  |  Container Management Platform"
Write-BoxLine ""
Write-BoxBottom
Write-Host ""

# ── 1. Check Python ──────────────────────────────────────────
Write-Step "Checking Python..."
$pyver = python --version 2>&1
if (-not "$pyver" -or "$pyver" -notmatch "Python") {
    # Try via winget
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  │  " -NoNewline -ForegroundColor $C
        Write-Host "Python not found – installing via winget..." -ForegroundColor $Y
        winget install Python.Python.3 --silent --accept-source-agreements 2>&1 | Out-Null
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pyver = python --version 2>&1
    }
    if (-not "$pyver" -or "$pyver" -notmatch "Python") {
        Write-Fail "Python not found.`n  Install from https://python.org then re-run."
    }
}
Write-StepOK "$pyver"

# ── 2. Determine install directory ───────────────────────────
if (Test-Path "$PWD\main.py") {
    $INSTALL_DIR = "$PWD"
} else {
    $INSTALL_DIR = "$PWD\ORCHIX"
}

# ── 3. Download source ───────────────────────────────────────
Write-Step "Downloading ORCHIX $ORCHIX_VERSION..."
if (Test-Path "$INSTALL_DIR\main.py") {
    Write-StepOK "Already installed at $INSTALL_DIR"
} else {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        git clone https://github.com/Sad-without-you/Orchix.git $INSTALL_DIR --quiet 2>&1 | Out-Null
    }
    if (-not (Test-Path "$INSTALL_DIR\main.py")) {
        $zipPath = "$env:TEMP\orchix_install.zip"
        $extractPath = "$env:TEMP\orchix_extract_$(Get-Random)"
        try {
            Invoke-WebRequest -Uri $GITHUB_ZIP -OutFile $zipPath -UseBasicParsing
            Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
            if (-not (Test-Path $INSTALL_DIR)) { New-Item -ItemType Directory -Path $INSTALL_DIR | Out-Null }
            Get-ChildItem "$extractPath\Orchix-main" | Move-Item -Destination $INSTALL_DIR -Force
        } catch {
            Write-Fail "Download failed – check your internet connection."
        } finally {
            Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
            Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    if (-not (Test-Path "$INSTALL_DIR\main.py")) { Write-Fail "Download failed – main.py not found." }
    Write-StepOK "Saved to $INSTALL_DIR"
}
Set-Location $INSTALL_DIR

# ── 4. Virtual environment ───────────────────────────────────
Write-Step "Creating Python virtual environment..."
if (-not (Test-Path ".venv")) { python -m venv .venv 2>&1 | Out-Null }
Write-StepOK ".venv ready"

# ── 5. Install dependencies ───────────────────────────────────
Write-Step "Installing dependencies..."
& ".venv\Scripts\python.exe" -m pip install --upgrade pip -q 2>&1 | Out-Null
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q 2>&1 | Out-Null
Write-StepOK "All packages installed"

# ── 6. Create PowerShell launcher (no CMD layer = no language issues) ──────
Write-Step "Creating launcher..."
@'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$ScriptDir\.venv\Scripts\python.exe" "$ScriptDir\main.py" @args
'@ | Set-Content -Path "orchix.ps1" -Encoding UTF8
# Also create .bat for CMD users
@"
@echo off
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0main.py" %*
"@ | Set-Content -Path "orchix.bat" -Encoding ASCII
# Allow running local PS1 scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force 2>&1 | Out-Null
Write-StepOK "orchix.ps1 + orchix.bat created"

# ── 7. Add ORCHIX to user PATH ───────────────────────────────
Write-Step "Adding ORCHIX to PATH..."
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$INSTALL_DIR*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$INSTALL_DIR", "User")
    $env:Path += ";$INSTALL_DIR"
    Write-StepOK "Added to PATH"
} else {
    Write-StepOK "Already in PATH"
}
Write-StepFinal "Done"

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-BoxTop "Green"
Write-BoxLine "" "Green"
Write-BoxLine "   OK  ORCHIX $ORCHIX_VERSION installed successfully!" "Green"
Write-BoxLine "" "Green"
Write-BoxLine "   Location:  $INSTALL_DIR" "Green"
Write-BoxLine "" "Green"
Write-BoxLine "   Launch (open a new terminal first):" "Green"
Write-BoxLine "   > orchix.ps1 --web    Web UI  ->  localhost:5000" "Green"
Write-BoxLine "   > orchix.ps1          CLI" "Green"
Write-BoxLine "" "Green"
Write-BoxLine "   Or in this terminal (dot-slash prefix):" "Green"
Write-BoxLine "   > .\orchix.ps1 --web" "Green"
Write-BoxLine "" "Green"
Write-BoxBottom "Green"
Write-Host ""
Read-Host "  Press Enter to exit"
