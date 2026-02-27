#!/bin/bash
# ============================================================
# ORCHIX v1.4 - Linux/macOS Installer
# ============================================================
# Run with: curl -sSL https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.sh | bash
# ============================================================

set -e

ORCHIX_VERSION="v1.4"
GITHUB_ZIP="https://github.com/Sad-without-you/Orchix/archive/refs/heads/main.zip"

# If already inside an ORCHIX directory, use current dir; otherwise create ORCHIX subdir
if [ -f "$(pwd)/main.py" ]; then
    INSTALL_DIR="$(pwd)"
else
    INSTALL_DIR="$(pwd)/ORCHIX"
fi

# ── Colors ───────────────────────────────────────────────────
CYN='\033[0;36m'; GRN='\033[0;32m'; YEL='\033[1;33m'
RED='\033[0;31m'; DGR='\033[2m';    BLD='\033[1m'; NC='\033[0m'

step()     { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}├──${NC} $1"; }
step_ok()  { echo -e "  ${CYN}│   ${GRN}OK${NC}  $1"; }
step_end() { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}└──${NC} ${GRN}OK${NC}  $1"; }
fail()     { echo -e "\n  ${CYN}└──${NC} ${RED}ERROR:${NC} $1\n"; exit 1; }

# ── Banner ───────────────────────────────────────────────────
clear 2>/dev/null || true
echo ""
echo -e "  ${CYN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${CYN}║                                                  ║${NC}"
echo -e "  ${CYN}║    ___  ____   ____ _   _ _____  __             ║${NC}"
echo -e "  ${CYN}║   / _ \\|  _ \\ / ___| | | |_ _\\ \\/ /            ║${NC}"
echo -e "  ${CYN}║  | | | | |_) | |   | |_| || | \\  /             ║${NC}"
echo -e "  ${CYN}║  | |_| |  _ <| |___|  _  || | /  \\             ║${NC}"
echo -e "  ${CYN}║   \\___/|_| \\_\\\\____|_| |_|___/_/\\_\\             ║${NC}"
echo -e "  ${CYN}║                                                  ║${NC}"
echo -e "  ${CYN}║   ${BLD}$ORCHIX_VERSION${NC}${CYN}  |  Container Management Platform       ║${NC}"
echo -e "  ${CYN}║                                                  ║${NC}"
echo -e "  ${CYN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Check Python ──────────────────────────────────────────
step "Checking Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done
[ -z "$PYTHON" ] && fail "Python 3.8+ required. Install:  sudo apt install python3"
PYVER=$($PYTHON --version 2>&1)
step_ok "$PYVER"

# ── 2. Download source ───────────────────────────────────────
step "Downloading ORCHIX $ORCHIX_VERSION..."
if [ -f "$INSTALL_DIR/main.py" ]; then
    step_ok "Already installed at $INSTALL_DIR"
    cd "$INSTALL_DIR"
elif [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR"
    command -v git &>/dev/null && git pull -q 2>/dev/null || true
    step_ok "Updated to latest"
else
    # Try git first, fall back to ZIP
    if command -v git &>/dev/null; then
        git clone -q https://github.com/Sad-without-you/Orchix.git "$INSTALL_DIR" 2>/dev/null || true
    fi
    if [ ! -f "$INSTALL_DIR/main.py" ]; then
        TMPZIP="/tmp/orchix_$$.zip"
        TMPDIR="/tmp/orchix_extract_$$"
        if command -v curl &>/dev/null; then
            curl -sL "$GITHUB_ZIP" -o "$TMPZIP" || fail "Download failed – check your connection."
        elif command -v wget &>/dev/null; then
            wget -q "$GITHUB_ZIP" -O "$TMPZIP" || fail "Download failed – check your connection."
        else
            fail "Neither git, curl, nor wget found. Please install one."
        fi
        mkdir -p "$INSTALL_DIR"
        unzip -q "$TMPZIP" -d "$TMPDIR" || fail "Failed to extract archive."
        mv "$TMPDIR"/Orchix-main/* "$INSTALL_DIR/"
        rm -rf "$TMPZIP" "$TMPDIR"
    fi
    [ ! -f "$INSTALL_DIR/main.py" ] && fail "Download failed – main.py not found."
    cd "$INSTALL_DIR"
    step_ok "Saved to $INSTALL_DIR"
fi

# ── 3. Virtual environment ───────────────────────────────────
step "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
fi
step_ok ".venv ready"

# ── 4. Install dependencies ───────────────────────────────────
step "Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q 2>/dev/null || true
pip install -r requirements.txt -q
step_ok "All packages installed"

# ── 5. Create launch script ──────────────────────────────────
step "Creating launcher..."
cat > orchix.sh <<'LAUNCH'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/main.py" "$@"
LAUNCH
chmod +x orchix.sh

GLOBAL_CMD="./orchix.sh"
if [ -w /usr/local/bin ]; then
    ln -sf "$(pwd)/orchix.sh" /usr/local/bin/orchix
    GLOBAL_CMD="orchix"
    step_end "orchix.sh created  (global: orchix)"
else
    step_end "orchix.sh created"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo -e "  ${GRN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GRN}║                                                  ║${NC}"
echo -e "  ${GRN}║   ${BLD}OK  ORCHIX $ORCHIX_VERSION installed successfully!${NC}${GRN}      ║${NC}"
echo -e "  ${GRN}║                                                  ║${NC}"
echo -e "  ${GRN}║   Location:  ${YEL}$INSTALL_DIR${GRN}"
echo -e "  ${GRN}║                                                  ║${NC}"
echo -e "  ${GRN}║   To launch ORCHIX:                             ║${NC}"
if [ "$GLOBAL_CMD" = "orchix" ]; then
echo -e "  ${GRN}║   ${CYN}$ orchix --web${GRN}   Web UI → localhost:5000      ║${NC}"
echo -e "  ${GRN}║   ${CYN}$ orchix      ${GRN}   CLI                          ║${NC}"
else
echo -e "  ${GRN}║   ${YEL}$ cd \"$INSTALL_DIR\"${GRN}"
echo -e "  ${GRN}║   ${CYN}$ ./orchix.sh --web${GRN}   Web UI → localhost:5000  ║${NC}"
echo -e "  ${GRN}║   ${CYN}$ ./orchix.sh      ${GRN}   CLI                      ║${NC}"
fi
echo -e "  ${GRN}║                                                  ║${NC}"
echo -e "  ${GRN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
