# ============================================================
# ORCHIX v1.4 - Windows PowerShell Installer
# ============================================================
# Run with: irm https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.ps1 | iex
# ============================================================

$ErrorActionPreference = "Stop"
$ORCHIX_VERSION = "v1.4"
$GITHUB_ZIP = "https://github.com/Sad-without-you/Orchix/archive/refs/heads/main.zip"
$INSTALL_DIR = "$PWD\ORCHIX"

function Write-Info  ($msg) { Write-Host "[ORCHIX] $msg" -ForegroundColor Cyan }
function Write-OK    ($msg) { Write-Host "[OK]     $msg" -ForegroundColor Green }
function Write-Warn  ($msg) { Write-Host "[WARN]   $msg" -ForegroundColor Yellow }
function Write-Fail  ($msg) { Write-Host "[ERROR]  $msg" -ForegroundColor Red; Read-Host "Press Enter to exit"; exit 1 }

Write-Host ""
Write-Host "  ORCHIX Container Management Platform  $ORCHIX_VERSION" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check Python ──────────────────────────────────────────
try {
    $pyver = python --version 2>&1
    Write-Info "Python found: $pyver"
} catch {
    Write-Fail "Python not found. Download from https://python.org and re-run this installer."
}

# ── 2. Download source ───────────────────────────────────────
if (Test-Path "$INSTALL_DIR\main.py") {
    Write-Info "Found existing ORCHIX directory."
} else {
    # Try git first
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        Write-Info "Cloning ORCHIX repository..."
        git clone https://github.com/Sad-without-you/Orchix.git $INSTALL_DIR
    } else {
        Write-Info "Downloading ORCHIX $ORCHIX_VERSION..."
        $zipPath = "$env:TEMP\orchix.zip"
        Invoke-WebRequest -Uri $GITHUB_ZIP -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\orchix_extract" -Force
        Move-Item "$env:TEMP\orchix_extract\Orchix-main" $INSTALL_DIR
        Remove-Item $zipPath -Force
        Remove-Item "$env:TEMP\orchix_extract" -Recurse -Force -ErrorAction SilentlyContinue
        Write-OK "Downloaded and extracted."
    }
}

Set-Location $INSTALL_DIR

# ── 3. Create virtual environment ────────────────────────────
if (-not (Test-Path ".venv")) {
    Write-Info "Creating Python virtual environment..."
    python -m venv .venv
}

# ── 4. Install dependencies ───────────────────────────────────
Write-Info "Installing dependencies (this may take a minute)..."
& ".venv\Scripts\pip.exe" install --upgrade pip -q
& ".venv\Scripts\pip.exe" install -r requirements.txt -q
Write-OK "Dependencies installed."

# ── 5. Create launch script ──────────────────────────────────
@"
@echo off
call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0main.py" %*
"@ | Set-Content -Path "orchix.bat" -Encoding ASCII

Write-Host ""
Write-OK "ORCHIX $ORCHIX_VERSION installed to: $INSTALL_DIR"
Write-Host ""
Write-Host "  To start ORCHIX:" -ForegroundColor White
Write-Host "    Web UI:  orchix.bat --web" -ForegroundColor Cyan
Write-Host "    CLI:     orchix.bat" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
