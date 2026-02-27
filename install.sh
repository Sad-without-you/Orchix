#!/bin/bash
# ============================================================
# ORCHIX v1.4 - Linux/macOS Installer
# ============================================================
# Solves:
#   - No git required (downloads ZIP from GitHub if needed)
#   - No --break-system-packages (uses isolated Python venv)
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

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[ORCHIX]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "  ██████╗ ██████╗  ██████╗██╗  ██╗██╗██╗  ██╗"
echo "  ██╔═══██╗██╔══██╗██╔════╝██║  ██║██║╚██╗██╔╝"
echo "  ██║   ██║██████╔╝██║     ███████║██║ ╚███╔╝ "
echo "  ██║   ██║██╔══██╗██║     ██╔══██║██║ ██╔██╗ "
echo "  ╚██████╔╝██║  ██║╚██████╗██║  ██║██║██╔╝ ██╗"
echo "   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝"
echo "  Container Management Platform  $ORCHIX_VERSION"
echo ""

# ── 1. Check Python ──────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done
[ -z "$PYTHON" ] && error "Python 3.8+ is required. Install it with: sudo apt install python3"
info "Python found: $($PYTHON --version)"

# ── 2. Download or update source ─────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Updating existing installation..."
    cd "$INSTALL_DIR"
    if command -v git &>/dev/null; then
        git pull
    else
        warning "git not found – cannot auto-update. Download the latest ZIP manually."
    fi
elif [ -d "$INSTALL_DIR" ]; then
    info "Found existing ORCHIX directory."
    cd "$INSTALL_DIR"
else
    if command -v git &>/dev/null; then
        info "Cloning ORCHIX repository..."
        git clone https://github.com/Sad-without-you/Orchix.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    else
        info "git not found – downloading ZIP instead..."
        if command -v curl &>/dev/null; then
            curl -L "$GITHUB_ZIP" -o /tmp/orchix.zip
        elif command -v wget &>/dev/null; then
            wget -O /tmp/orchix.zip "$GITHUB_ZIP"
        else
            error "Neither git, curl, nor wget found. Please install one of them."
        fi
        unzip -q /tmp/orchix.zip -d /tmp/orchix_extract
        mv /tmp/orchix_extract/Orchix-main "$INSTALL_DIR"
        rm -rf /tmp/orchix.zip /tmp/orchix_extract
        cd "$INSTALL_DIR"
        info "Downloaded and extracted ORCHIX $ORCHIX_VERSION"
    fi
fi

# ── 3. Create virtual environment ────────────────────────────
if [ ! -d ".venv" ]; then
    info "Creating Python virtual environment..."
    $PYTHON -m venv .venv
fi

# ── 4. Install dependencies ───────────────────────────────────
info "Installing dependencies (this may take a minute)..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
info "Dependencies installed."

# ── 5. Create launch script ──────────────────────────────────
cat > orchix.sh <<'LAUNCH'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
python "$SCRIPT_DIR/main.py" "$@"
LAUNCH
chmod +x orchix.sh

# ── 6. Optional: symlink to /usr/local/bin ───────────────────
if [ -w /usr/local/bin ]; then
    ln -sf "$(pwd)/orchix.sh" /usr/local/bin/orchix
    info "Installed to /usr/local/bin/orchix – you can now run: orchix"
else
    info "Run ORCHIX with: ./orchix.sh  (or: bash orchix.sh)"
    info "To install globally: sudo ln -sf $(pwd)/orchix.sh /usr/local/bin/orchix"
fi

echo ""
info "ORCHIX $ORCHIX_VERSION installed successfully!"
echo ""
