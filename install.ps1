# ============================================================
# ORCHIX v1.4 - Windows PowerShell Installer
# ============================================================
# Run with: irm https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.ps1 | iex
# ============================================================

$ErrorActionPreference = "Stop"
$ORCHIX_VERSION = "v1.4"
$GITHUB_ZIP = "https://github.com/Sad-without-you/Orchix/archive/refs/heads/main.zip"
$C = "Cyan"; $G = "Green"; $DG = "DarkGray"; $W = "White"; $R = "Red"; $Y = "Yellow"

function Write-Fail($msg) {
    Write-Host "`n  └── " -NoNewline -ForegroundColor $C
    Write-Host "ERROR: $msg" -ForegroundColor $R
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}
function Write-Step($msg) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  ├── " -NoNewline -ForegroundColor $C
    Write-Host $msg -ForegroundColor $W
}
function Write-StepOK($msg) {
    Write-Host "  │   " -NoNewline -ForegroundColor $C
    Write-Host "OK  " -NoNewline -ForegroundColor $G
    Write-Host $msg -ForegroundColor DarkGreen
}
function Write-StepFinal($msg) {
    Write-Host "  │" -ForegroundColor $C
    Write-Host "  └── " -NoNewline -ForegroundColor $C
    Write-Host "OK  " -NoNewline -ForegroundColor $G
    Write-Host $msg -ForegroundColor DarkGreen
}

# ── Banner ───────────────────────────────────────────────────
Clear-Host
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor $C
Write-Host "  ║                                                  ║" -ForegroundColor $C
Write-Host "  ║    ___  ____   ____ _   _ _____  __             ║" -ForegroundColor $C
Write-Host "  ║   / _ \|  _ \ / ___| | | |_ _\ \/ /            ║" -ForegroundColor $C
Write-Host "  ║  | | | | |_) | |   | |_| || | \  /             ║" -ForegroundColor $C
Write-Host "  ║  | |_| |  _ <| |___|  _  || | /  \             ║" -ForegroundColor $C
Write-Host "  ║   \___/|_| \_\\____|_| |_|___/_/\_\             ║" -ForegroundColor $C
Write-Host "  ║                                                  ║" -ForegroundColor $C
Write-Host "  ║   $ORCHIX_VERSION  |  Container Management Platform       ║" -ForegroundColor $C
Write-Host "  ║                                                  ║" -ForegroundColor $C
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor $C
Write-Host ""

# ── 1. Check Python ──────────────────────────────────────────
Write-Step "Checking Python..."
$pyver = python --version 2>&1
if (-not "$pyver") { Write-Fail "Python not found. Download from https://python.org" }
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

# ── 6. Create launch script ──────────────────────────────────
Write-Step "Creating launcher..."
@"
@echo off
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0main.py" %*
"@ | Set-Content -Path "orchix.bat" -Encoding ASCII
Write-StepFinal "orchix.bat created"

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor $G
Write-Host "  ║                                                  ║" -ForegroundColor $G
Write-Host "  ║   OK  ORCHIX $ORCHIX_VERSION installed successfully!      ║" -ForegroundColor $G
Write-Host "  ║                                                  ║" -ForegroundColor $G
Write-Host "  ║   Location:                                      ║" -ForegroundColor $G
Write-Host "  ║   $INSTALL_DIR" -NoNewline -ForegroundColor $Y
$pad = " " * [Math]::Max(0, 50 - $INSTALL_DIR.Length)
Write-Host "$pad║" -ForegroundColor $G
Write-Host "  ║                                                  ║" -ForegroundColor $G
Write-Host "  ║   To launch ORCHIX:                             ║" -ForegroundColor $G
Write-Host "  ║   > " -NoNewline -ForegroundColor $G
Write-Host "cd `"$INSTALL_DIR`"" -NoNewline -ForegroundColor $Y
$pad2 = " " * [Math]::Max(0, 45 - $INSTALL_DIR.Length)
Write-Host "$pad2║" -ForegroundColor $G
Write-Host "  ║   > " -NoNewline -ForegroundColor $G
Write-Host "orchix.bat --web" -NoNewline -ForegroundColor $C
Write-Host "   Web UI  →  localhost:5000    ║" -ForegroundColor $G
Write-Host "  ║   > " -NoNewline -ForegroundColor $G
Write-Host "orchix.bat      " -NoNewline -ForegroundColor $C
Write-Host "   CLI                          ║" -ForegroundColor $G
Write-Host "  ║                                                  ║" -ForegroundColor $G
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor $G
Write-Host ""
Read-Host "  Press Enter to exit"
