#!/bin/bash
# ============================================================
# ORCHIX v1.4 - Linux/macOS Installer
# ============================================================
# Run with: curl -sSL https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.sh | bash
# ============================================================

set -e

ORCHIX_VERSION="v1.4"
GITHUB_ZIP="https://github.com/Sad-without-you/Orchix/archive/refs/heads/main.zip"
BW=54  # box inner width

if [ -f "$(pwd)/main.py" ]; then
    INSTALL_DIR="$(pwd)"
else
    INSTALL_DIR="$(pwd)/ORCHIX"
fi

# ── Colors ───────────────────────────────────────────────────
CYN='\033[0;36m'; GRN='\033[0;32m'; YEL='\033[1;33m'
RED='\033[0;31m'; BLD='\033[1m'; NC='\033[0m'

box_line() {
    local text="${1:-}"
    local color="${2:-$CYN}"
    local pad=$(( BW - ${#text} ))
    printf "  ${color}║${NC}%s%${pad}s${color}║${NC}\n" "$text" ""
}
box_top()    { local c="${1:-$CYN}"; printf "  ${c}╔%0.s═%.0s${NC}\n" $(seq 1 $BW) | head -c $((BW+4)); echo -e "  ${c}╔$(printf '═%.0s' $(seq 1 $BW))╗${NC}"; }
box_bottom() { local c="${1:-$CYN}"; echo -e "  ${c}╚$(printf '═%.0s' $(seq 1 $BW))╝${NC}"; }

step()      { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}├─${NC} $1"; }
step_ok()   { echo -e "  ${CYN}│  ${GRN}OK${NC} $1"; }
step_end()  { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}└─${NC} ${GRN}OK${NC} $1"; }
fail()      { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}└─${NC} ${RED}ERROR:${NC} $1\n"; exit 1; }

# ── Banner ───────────────────────────────────────────────────
clear 2>/dev/null || true
echo ""
box_top "$CYN"
box_line ""
box_line "   ___  ____   ____ _   _ _____  __"
box_line "  / _ \|  _ \ / ___| | | |_ _\ \/ /"
box_line " | | | | |_) | |   | |_| || | \  / "
box_line " | |_| |  _ <| |___|  _  || | /  \ "
box_line "  \___/|_| \_\\\\____|_| |_|___/_/\_\\"
box_line ""
box_line "   $ORCHIX_VERSION  |  Container Management Platform"
box_line ""
box_bottom "$CYN"
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

if [ -z "$PYTHON" ]; then
    echo -e "  ${CYN}│  ${YEL}Python 3.8+ not found – trying to install...${NC}"
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3 python3-venv -q && PYTHON="python3"
    elif command -v brew &>/dev/null; then
        brew install python3 && PYTHON="python3"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 -q && PYTHON="python3"
    fi
    [ -z "$PYTHON" ] && fail "Python not found. Install with:  sudo apt install python3"
fi
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

LAUNCH_CMD="./orchix.sh"
if [ -w /usr/local/bin ]; then
    ln -sf "$(pwd)/orchix.sh" /usr/local/bin/orchix
    LAUNCH_CMD="orchix"
    step_end "orchix.sh created  (global: orchix)"
else
    step_end "orchix.sh created"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
box_top "$GRN"
box_line "" "$GRN"
box_line "   OK  ORCHIX $ORCHIX_VERSION installed successfully!" "$GRN"
box_line "" "$GRN"
box_line "   Location:  $INSTALL_DIR" "$GRN"
box_line "" "$GRN"
box_line "   Background Web UI (no terminal needed):" "$GRN"
if [ "$LAUNCH_CMD" = "orchix" ]; then
box_line "   \$ orchix service start   # Start in background" "$GRN"
box_line "   \$ orchix service stop    # Stop" "$GRN"
box_line "" "$GRN"
box_line "   Or run directly:" "$GRN"
box_line "   \$ orchix --web    Web UI  →  localhost:5000" "$GRN"
box_line "   \$ orchix          CLI" "$GRN"
else
box_line "   \$ cd \"$INSTALL_DIR\"" "$GRN"
box_line "   \$ ./orchix.sh service start    # Start in background" "$GRN"
box_line "   \$ ./orchix.sh service stop     # Stop" "$GRN"
box_line "" "$GRN"
box_line "   Or run directly:" "$GRN"
box_line "   \$ ./orchix.sh --web    Web UI  →  localhost:5000" "$GRN"
box_line "   \$ ./orchix.sh          CLI" "$GRN"
fi
box_line "" "$GRN"
box_bottom "$GRN"
echo ""

# ── Optional: Start Web UI as background service ──────────────────────────────
printf "  ${CYN}│${NC}\n"
printf "  ${CYN}├─${NC} Start ORCHIX Web UI now (background)? [Y/n]: "
read -r start_now
if [[ ! "$start_now" =~ ^[Nn] ]]; then
    "$PYTHON" "$INSTALL_DIR/main.py" service start
    printf "  ${CYN}│${NC}\n"
    printf "  ${CYN}├─${NC} Enable autostart on boot? [Y/n]: "
    read -r autostart
    if [[ ! "$autostart" =~ ^[Nn] ]]; then
        "$PYTHON" "$INSTALL_DIR/main.py" service enable
    fi
fi
echo ""
