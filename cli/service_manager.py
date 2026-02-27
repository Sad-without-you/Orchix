import os
import sys
import subprocess
import platform
import signal
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

INSTALL_DIR = Path(__file__).parent.parent
CONFIG_DIR = Path.home() / '.orchix_configs'
PID_FILE = CONFIG_DIR / 'orchix.pid'
LOG_FILE = CONFIG_DIR / 'orchix.log'
SERVICE_NAME = 'orchix'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _has_systemd():
    try:
        result = subprocess.run(
            ['systemctl', '--user', '--no-pager', 'status'],
            capture_output=True, timeout=3
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _get_python():
    if platform.system() == 'Windows':
        pythonw = INSTALL_DIR / '.venv' / 'Scripts' / 'pythonw.exe'
        if pythonw.exists():
            return str(pythonw)
        return str(INSTALL_DIR / '.venv' / 'Scripts' / 'python.exe')
    return str(INSTALL_DIR / '.venv' / 'bin' / 'python')


def _get_main():
    return str(INSTALL_DIR / 'main.py')


def _is_process_running(pid):
    if HAS_PSUTIL:
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_pid():
    try:
        if PID_FILE.exists():
            return int(PID_FILE.read_text().strip())
    except (ValueError, IOError):
        pass
    return None


def _write_pid(pid):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def _delete_pid():
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _use_systemd():
    return platform.system() != 'Windows' and _has_systemd()


# ── systemd unit ──────────────────────────────────────────────────────────────

def _ensure_systemd_unit():
    unit_dir = Path.home() / '.config' / 'systemd' / 'user'
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_file = unit_dir / f'{SERVICE_NAME}.service'

    python = _get_python()
    main = _get_main()
    log = str(LOG_FILE)

    content = f"""[Unit]
Description=ORCHIX Web UI
After=network.target

[Service]
Type=simple
ExecStart={python} {main} --web
Restart=on-failure
RestartSec=5
StandardOutput=append:{log}
StandardError=append:{log}

[Install]
WantedBy=default.target
"""
    unit_file.write_text(content)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)


# ── Status ────────────────────────────────────────────────────────────────────

def get_status():
    if _use_systemd():
        result = subprocess.run(
            ['systemctl', '--user', 'is-active', SERVICE_NAME],
            capture_output=True, text=True
        )
        running = result.returncode == 0
        pid = _read_pid()
        return {'running': running, 'pid': pid, 'method': 'systemd'}

    pid = _read_pid()
    if pid and _is_process_running(pid):
        return {'running': True, 'pid': pid, 'method': 'pid'}

    if pid:
        _delete_pid()
    return {'running': False, 'pid': None, 'method': 'pid'}


# ── Start ─────────────────────────────────────────────────────────────────────

def start_service():
    status = get_status()
    if status['running']:
        print(f"  ✅ ORCHIX Web UI is already running (PID {status['pid']})")
        print(f"  ℹ️  Open http://localhost:5000 in your browser")
        return True

    if _use_systemd():
        _ensure_systemd_unit()
        result = subprocess.run(
            ['systemctl', '--user', 'start', SERVICE_NAME],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  ✅ ORCHIX Web UI started")
            print("  ℹ️  Open http://localhost:5000 in your browser")
            return True
        print(f"  ❌ Failed to start: {result.stderr.strip()}")
        return False

    return _start_process()


def _start_process():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    python = _get_python()
    main = _get_main()

    with open(LOG_FILE, 'a') as log:
        if platform.system() == 'Windows':
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            proc = subprocess.Popen(
                [python, main, '--web'],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                stdout=log,
                stderr=log,
                cwd=str(INSTALL_DIR)
            )
        else:
            proc = subprocess.Popen(
                [python, main, '--web'],
                stdout=log,
                stderr=log,
                cwd=str(INSTALL_DIR),
                start_new_session=True
            )

    _write_pid(proc.pid)
    print(f"  ✅ ORCHIX Web UI started (PID {proc.pid})")
    print(f"  ℹ️  Open http://localhost:5000 in your browser")
    print(f"  ℹ️  Logs: {LOG_FILE}")
    return True


# ── Stop ──────────────────────────────────────────────────────────────────────

def stop_service():
    status = get_status()
    if not status['running']:
        print("  ℹ️  ORCHIX Web UI is not running")
        return True

    if status['method'] == 'systemd':
        result = subprocess.run(
            ['systemctl', '--user', 'stop', SERVICE_NAME],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            _delete_pid()
            print("  ✅ ORCHIX Web UI stopped")
            return True
        print(f"  ❌ Failed to stop: {result.stderr.strip()}")
        return False

    pid = status['pid']
    try:
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
        _delete_pid()
        print(f"  ✅ ORCHIX Web UI stopped (PID {pid})")
        return True
    except Exception as e:
        print(f"  ❌ Failed to stop: {e}")
        return False


# ── Enable / Disable autostart ────────────────────────────────────────────────

def enable_autostart():
    if _use_systemd():
        _ensure_systemd_unit()
        subprocess.run(['systemctl', '--user', 'enable', SERVICE_NAME], capture_output=True)
        user = os.environ.get('USER') or os.environ.get('LOGNAME') or ''
        if user:
            subprocess.run(['loginctl', 'enable-linger', user], capture_output=True)
        print("  ✅ Autostart enabled — ORCHIX Web UI will start on boot")
        return True

    if platform.system() == 'Windows':
        python = _get_python()
        main = _get_main()
        result = subprocess.run([
            'schtasks', '/create', '/f',
            '/sc', 'ONLOGON',
            '/tn', 'ORCHIX-WebUI',
            '/tr', f'"{python}" "{main}" --web',
            '/rl', 'HIGHEST'
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Autostart enabled — ORCHIX Web UI will start on login")
            return True
        print(f"  ❌ Failed to enable autostart: {result.stderr.strip()}")
        return False

    print("  ⚠️  Systemd not found. Add 'orchix service start' to your startup scripts manually.")
    return False


def disable_autostart():
    if _use_systemd():
        subprocess.run(['systemctl', '--user', 'disable', SERVICE_NAME], capture_output=True)
        print("  ✅ Autostart disabled")
        return True

    if platform.system() == 'Windows':
        subprocess.run(['schtasks', '/delete', '/tn', 'ORCHIX-WebUI', '/f'], capture_output=True)
        print("  ✅ Autostart disabled")
        return True

    return False


# ── Print status ──────────────────────────────────────────────────────────────

def _print_status():
    status = get_status()
    if status['running']:
        pid_str = f" (PID {status['pid']})" if status['pid'] else ''
        print(f"  ✅ ORCHIX Web UI is running{pid_str}")
        print(f"  ℹ️  URL: http://localhost:5000")
    else:
        print("  ℹ️  ORCHIX Web UI is not running")
        print("  ℹ️  Run: orchix service start")


# ── Uninstall service entries ─────────────────────────────────────────────────

def uninstall_service():
    """Remove all service/autostart entries (does NOT delete the ORCHIX directory)"""
    stop_service()
    disable_autostart()

    # Remove systemd unit file
    if platform.system() != 'Windows':
        unit_file = Path.home() / '.config' / 'systemd' / 'user' / f'{SERVICE_NAME}.service'
        if unit_file.exists():
            unit_file.unlink()
            subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)
            print("  ✅ Systemd unit removed")

    # Remove PID and log files
    _delete_pid()
    try:
        LOG_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    print("  ✅ ORCHIX service entries removed")
    print("  ℹ️  To fully uninstall, also delete the ORCHIX folder and ~/.orchix_configs/")


# ── Main handler ──────────────────────────────────────────────────────────────

def handle_service_command(action: str):
    actions = {
        'start':     start_service,
        'stop':      stop_service,
        'status':    _print_status,
        'enable':    enable_autostart,
        'disable':   disable_autostart,
        'uninstall': uninstall_service,
    }

    if action not in actions:
        print(f"  ❌ Unknown action: '{action}'")
        print("  Usage: orchix service [start|stop|status|enable|disable|uninstall]")
        return

    actions[action]()
