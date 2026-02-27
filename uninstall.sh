#!/bin/bash
# ============================================================
# ORCHIX - Uninstaller (Linux/macOS)
# ============================================================

BW=54
CYN='\033[0;36m'; GRN='\033[0;32m'; YEL='\033[1;33m'
RED='\033[0;31m'; BLD='\033[1m'; NC='\033[0m'

box_line() { local text="${1:-}"; local color="${2:-$CYN}"; local pad=$(( BW - ${#text} )); printf "  ${color}║${NC}%s%${pad}s${color}║${NC}\n" "$text" ""; }
box_top()    { local c="${1:-$CYN}"; echo -e "  ${c}╔$(printf '═%.0s' $(seq 1 $BW))╗${NC}"; }
box_bottom() { local c="${1:-$CYN}"; echo -e "  ${c}╚$(printf '═%.0s' $(seq 1 $BW))╝${NC}"; }
step()      { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}├─${NC} $1"; }
step_ok()   { echo -e "  ${CYN}│  ${GRN}OK${NC} $1"; }
step_end()  { echo -e "  ${CYN}│${NC}"; echo -e "  ${CYN}└─${NC} ${GRN}OK${NC} $1"; }
fail()      { echo -e "  ${CYN}└─${NC} ${RED}ERROR:${NC} $1\n"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clear 2>/dev/null || true
echo ""
box_top "$RED"
box_line ""
box_line "   ___  ____   ____ _   _ _____  __"
box_line "  / _ \|  _ \ / ___| | | |_ _\ \/ /"
box_line " | | | | |_) | |   | |_| || | \  / "
box_line " | |_| |  _ <| |___|  _  || | /  \ "
box_line "  \___/|_| \_\\____|_| |_|___/_/\_\\"
box_line ""
box_line "   Uninstall"
box_line ""
box_bottom "$RED"
echo ""

# ── 1. Stop and remove service ────────────────────────────────────────────────
step "Stopping ORCHIX Web UI service..."
PYTHON=""
for cmd in "$SCRIPT_DIR/.venv/bin/python" python3 python; do
    if command -v "$cmd" &>/dev/null || [ -f "$cmd" ]; then
        PYTHON="$cmd"
        break
    fi
done

if [ -n "$PYTHON" ] && [ -f "$SCRIPT_DIR/main.py" ]; then
    "$PYTHON" "$SCRIPT_DIR/main.py" service uninstall 2>/dev/null || true
    step_ok "Service stopped and removed"
else
    # Fallback: manual cleanup
    systemctl --user stop orchix 2>/dev/null || true
    systemctl --user disable orchix 2>/dev/null || true
    rm -f ~/.config/systemd/user/orchix.service 2>/dev/null || true
    systemctl --user daemon-reload 2>/dev/null || true
    step_ok "Service entries removed"
fi

# ── 2. Remove global symlink ──────────────────────────────────────────────────
step "Removing global launcher..."
if [ -L /usr/local/bin/orchix ]; then
    rm -f /usr/local/bin/orchix 2>/dev/null || sudo rm -f /usr/local/bin/orchix 2>/dev/null || true
    step_ok "Removed /usr/local/bin/orchix"
else
    step_ok "No global launcher found"
fi

# ── 3. Ask about config data ──────────────────────────────────────────────────
step "Config & data files..."
CONFIG_DIR="$HOME/.orchix_configs"
if [ -d "$CONFIG_DIR" ]; then
    echo -e "  ${CYN}│${NC}"
    printf "  ${CYN}│${NC}     Remove config/data at $CONFIG_DIR? [y/N]: "
    read -r remove_config
    if [[ "$remove_config" =~ ^[Yy] ]]; then
        rm -rf "$CONFIG_DIR"
        step_ok "Config directory removed"
    else
        step_ok "Config directory kept"
    fi
else
    step_ok "No config directory found"
fi

# ── 4. Remove ORCHIX directory ────────────────────────────────────────────────
step "Removing ORCHIX installation..."
echo -e "  ${CYN}│${NC}"
printf "  ${CYN}│${NC}     Delete $SCRIPT_DIR? [y/N]: "
read -r remove_dir
if [[ "$remove_dir" =~ ^[Yy] ]]; then
    # Can't delete the running script's dir directly — schedule removal
    echo -e "  ${CYN}│${NC}     Scheduling removal..."
    (sleep 1 && rm -rf "$SCRIPT_DIR") &
    step_end "ORCHIX will be removed in a moment"
else
    step_end "Skipped (directory kept)"
fi

echo ""
box_top "$GRN"
box_line "" "$GRN"
box_line "   ORCHIX uninstalled successfully" "$GRN"
box_line "" "$GRN"
box_bottom "$GRN"
echo ""
