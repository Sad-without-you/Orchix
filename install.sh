#!/bin/bash
# ============================================================
# ORCHIX v1.4 - Linux/macOS Installer
# ============================================================
# Run with: curl -sSL https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.sh | bash
# ============================================================

# ── curl|bash guard ──────────────────────────────────────────────────────────
# When piped (curl | bash), bash reads the script from stdin, so `read`
# commands have no terminal to read from. Fix: save the rest of the script to
# a temp file and re-exec it with /dev/tty as stdin.
[ -t 0 ] || { _T=$(mktemp /tmp/orchix_XXXXXX.sh); cat > "$_T"; exec bash "$_T" </dev/tty 2>/dev/null || exec bash "$_T"; exit; }

# ── Pre-authenticate sudo once ───────────────────────────────
if [ "$(id -u)" -ne 0 ] && command -v sudo &>/dev/null; then
    echo "  → Some steps require root privileges."
    echo "  → Please enter your sudo password once:"
    if ! sudo -v; then
        echo -e "  ${RED}ERROR:${NC} sudo authentication failed. Please re-run the installer."
        exit 1
    fi
fi

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
box_top()    { local c="${1:-$CYN}"; echo -e "  ${c}╔$(printf '═%.0s' $(seq 1 $BW))╗${NC}"; }
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
box_line "   $ORCHIX_VERSION  |  Container Management System"
box_line ""
box_bottom "$CYN"
echo ""

# ── 1. Check Python ──────────────────────────────────────────
step "Checking Python..."
PYTHON=""

# Helper: returns 0 if $1 is Python 3.12+
_py_ok() {
    local cmd="$1"
    command -v "$cmd" &>/dev/null || return 1
    local minor major
    major=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null) || return 1
    minor=$("$cmd" -c "import sys; print(sys.version_info.minor)"  2>/dev/null) || return 1
    [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]
}

for cmd in python3.14 python3.13 python3.12 python3 python; do
    if _py_ok "$cmd"; then PYTHON="$cmd"; break; fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${CYN}│  ${YEL}Python 3.12+ not found – installing...${NC}"

    if command -v apt-get &>/dev/null; then
        # Detect distro: Ubuntu gets deadsnakes PPA, Debian gets backports
        DISTRO=$(grep -oP '(?<=^ID=).+' /etc/os-release 2>/dev/null | tr -d '"' || echo "unknown")
        CODENAME=$(grep -oP '(?<=^VERSION_CODENAME=).+' /etc/os-release 2>/dev/null | tr -d '"' || lsb_release -cs 2>/dev/null || echo "")

        DEBIAN_FRONTEND=noninteractive sudo apt-get update -qq >/dev/null 2>&1 || true
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y python3.12 python3.12-venv -qq >/dev/null 2>&1 || true

        if ! command -v python3.12 &>/dev/null; then
            case "$DISTRO" in
                ubuntu)
                    echo -e "  ${CYN}│  ${YEL}Adding deadsnakes PPA (Ubuntu)...${NC}"
                    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y software-properties-common -qq >/dev/null 2>&1 || true
                    sudo add-apt-repository -y ppa:deadsnakes/ppa >/dev/null 2>&1 || true
                    DEBIAN_FRONTEND=noninteractive sudo apt-get update -qq >/dev/null 2>&1 || true
                    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y python3.12 python3.12-venv -qq >/dev/null 2>&1 || true
                    ;;
                debian|raspbian)
                    if [ -n "$CODENAME" ]; then
                        echo -e "  ${CYN}│  ${YEL}Trying Debian backports (${CODENAME})...${NC}"
                        echo "deb http://deb.debian.org/debian ${CODENAME}-backports main" | \
                            sudo tee /etc/apt/sources.list.d/orchix-backports.list >/dev/null 2>&1 || true
                        DEBIAN_FRONTEND=noninteractive sudo apt-get update -qq >/dev/null 2>&1 || true
                        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -t "${CODENAME}-backports" python3.12 python3.12-venv -qq >/dev/null 2>&1 || true
                    fi
                    ;;
            esac
        fi
        command -v python3.12 &>/dev/null && PYTHON="python3.12"

    elif command -v dnf &>/dev/null; then
        sudo dnf makecache -q >/dev/null 2>&1 || true
        sudo dnf install -y python3.12 -q >/dev/null 2>&1 || true
        command -v python3.12 &>/dev/null && PYTHON="python3.12"

    elif command -v pacman &>/dev/null; then
        sudo pacman -Sy --noconfirm >/dev/null 2>&1 || true
        sudo pacman -S --noconfirm python >/dev/null 2>&1 || true
        for cmd in python3.12 python3; do
            _py_ok "$cmd" && PYTHON="$cmd" && break || true
        done

    elif command -v zypper &>/dev/null; then
        sudo zypper refresh >/dev/null 2>&1 || true
        sudo zypper install -y python312 >/dev/null 2>&1 || true
        command -v python3.12 &>/dev/null && PYTHON="python3.12"

    elif command -v brew &>/dev/null; then
        brew update >/dev/null 2>&1 || true
        brew install python@3.12 >/dev/null 2>&1 || true
        for cmd in "$(brew --prefix 2>/dev/null)/bin/python3.12" python3.12; do
            _py_ok "$cmd" 2>/dev/null && PYTHON="$cmd" && break || true
        done
    fi

    if [ -z "$PYTHON" ]; then
        if command -v apt-get &>/dev/null && [ "$DISTRO" = "ubuntu" ]; then
            _HINT="  sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.12"
        elif command -v apt-get &>/dev/null; then
            _HINT="  sudo apt install python3.12    (or: sudo apt install -t ${CODENAME}-backports python3.12)"
        elif command -v dnf &>/dev/null; then
            _HINT="  sudo dnf install python3.12"
        else
            _HINT="  See https://python.org/downloads"
        fi
        fail "Python 3.12+ could not be installed automatically.\n  Install manually:\n${_HINT}"
    fi
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
rm -rf .venv 2>/dev/null || true
PYMAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "3")
PYMINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "12")
if ! $PYTHON -m venv .venv 2>/dev/null; then
    echo -e "  ${CYN}│  ${YEL}python3-venv not found – installing...${NC}"
    if command -v apt-get &>/dev/null; then
        DEBIAN_FRONTEND=noninteractive sudo apt-get update -qq >/dev/null 2>&1 || true
        # Try versioned package first (python3.12-venv), then generic
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y "python${PYMAJOR}.${PYMINOR}-venv" -qq >/dev/null 2>&1 || \
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y python3-venv -qq >/dev/null 2>&1 || true
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-virtualenv -q >/dev/null 2>&1 || true
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-virtualenv >/dev/null 2>&1 || true
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y python3-venv >/dev/null 2>&1 || true
    fi
    if ! $PYTHON -c "import venv" 2>/dev/null; then
        fail "venv module unavailable.\n  Run: sudo apt install python${PYMAJOR}.${PYMINOR}-venv"
    fi
    $PYTHON -m venv .venv || fail "Failed to create virtual environment.\n  Run: sudo apt install python${PYMAJOR}.${PYMINOR}-venv"
fi
step_ok ".venv ready"

# ── 4. Install dependencies ───────────────────────────────────
step "Installing dependencies..."
source .venv/bin/activate
.venv/bin/pip install --upgrade pip -q >/dev/null 2>&1 || \
    echo -e "  ${CYN}│  ${YEL}⚠  pip upgrade skipped (non-critical)${NC}"

if ! PIP_OUT=$(.venv/bin/pip install -r requirements.txt -q 2>&1); then
    echo -e "  ${CYN}│  ${RED}Package install failed:${NC}"
    echo "$PIP_OUT" | while IFS= read -r line; do
        [ -n "$line" ] && echo -e "  ${CYN}│    ${YEL}${line}${NC}"
    done
    fail "Dependency install failed – run:  .venv/bin/pip install -r requirements.txt"
fi
step_ok "All packages installed"

# ── 5. Create launch script ──────────────────────────────────
step "Creating launcher..."
# Write absolute INSTALL_DIR into the launcher — works even when symlinked
cat > orchix.sh <<LAUNCH
#!/bin/bash
"$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/main.py" "\$@"
LAUNCH
chmod +x orchix.sh

LAUNCH_CMD="./orchix.sh"
if [ -w /usr/local/bin ]; then
    ln -sf "$(pwd)/orchix.sh" /usr/local/bin/orchix
    LAUNCH_CMD="orchix"
    step_end "orchix.sh created  (global: orchix)"
elif sudo ln -sf "$(pwd)/orchix.sh" /usr/local/bin/orchix 2>/dev/null; then
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
if [ "$LAUNCH_CMD" = "orchix" ]; then
box_line "   Web UI:  http://localhost:5000" "$GRN"
box_line "   CLI:     orchix" "$GRN"
box_line "" "$GRN"
box_line "   orchix service stop    # Stop Web UI" "$GRN"
box_line "   orchix service status  # Check status" "$GRN"
else
box_line "   Web UI:  http://localhost:5000" "$GRN"
box_line "   CLI:     ./orchix.sh" "$GRN"
box_line "" "$GRN"
box_line "   \$ cd \"$INSTALL_DIR\"" "$GRN"
box_line "   \$ ./orchix.sh service stop    # Stop Web UI" "$GRN"
box_line "   \$ ./orchix.sh service status  # Check status" "$GRN"
fi
box_line "" "$GRN"
box_bottom "$GRN"
echo ""

# ── Docker daemon + group ─────────────────────────────────────────────────────
DOCKER_GROUP_ADDED=false
if command -v docker &>/dev/null; then
    # Start Docker daemon if not running
    if ! docker info &>/dev/null 2>&1; then
        step "Starting Docker daemon..."
        sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null || true
        sleep 2
        if docker info &>/dev/null 2>&1; then
            step_ok "Docker daemon started"
        else
            echo -e "  ${CYN}│  ${YEL}⚠  Docker not responding — run: sudo systemctl start docker${NC}"
        fi
    fi
    # Add user to docker group if missing
    if ! groups 2>/dev/null | grep -qw docker; then
        step "Adding $USER to docker group..."
        if sudo usermod -aG docker "$USER" 2>/dev/null; then
            DOCKER_GROUP_ADDED=true
            step_ok "Added — no re-login needed (using sg docker)"
        fi
    fi
fi

# ── Optional: Start Web UI as background service ──────────────────────────────
VENV_PYTHON="$INSTALL_DIR/.venv/bin/python"
printf "  ${CYN}│${NC}\n"
if ! docker info &>/dev/null 2>&1; then
    echo -e "  ${CYN}│  ${YEL}⚠  Docker is not running — skipping Web UI auto-start${NC}"
    echo -e "  ${CYN}│  ${YEL}   Start Docker first, then run: orchid service start${NC}"
else
    printf "  ${CYN}├─${NC} Start ORCHIX Web UI now (background)? [Y/n]: "
    read -r start_now || start_now=""
    if [[ ! "$start_now" =~ ^[Nn] ]]; then
        "$VENV_PYTHON" "$INSTALL_DIR/main.py" init-users </dev/null || true
        if $DOCKER_GROUP_ADDED; then
            sg docker -c "\"$VENV_PYTHON\" \"$INSTALL_DIR/main.py\" service start" </dev/null 2>/dev/null || \
            "$VENV_PYTHON" "$INSTALL_DIR/main.py" service start </dev/null 2>&1 || \
            echo -e "  ${CYN}│  ${YEL}⚠  Web UI failed to start — check: ~/.orchix_configs/orchix.log${NC}"
        else
            "$VENV_PYTHON" "$INSTALL_DIR/main.py" service start </dev/null 2>&1 || \
            echo -e "  ${CYN}│  ${YEL}⚠  Web UI failed to start — check: ~/.orchix_configs/orchix.log${NC}"
        fi
    fi
fi
# Flush any buffered input (e.g. Enter pressed during service start) before next prompt
read -r -t 0.1 -n 10000 _flush </dev/tty 2>/dev/null || true
printf "  ${CYN}│${NC}\n"
printf "  ${CYN}├─${NC} Enable autostart on boot? [Y/n]: "
read -r auto_start || auto_start=""
if [[ ! "$auto_start" =~ ^[Nn] ]]; then
    "$VENV_PYTHON" "$INSTALL_DIR/main.py" service enable </dev/null || true
    echo -e "  ${CYN}│  ${NC}ℹ  Autostart on boot enabled — ORCHIX Web UI starts automatically"
fi
echo ""
