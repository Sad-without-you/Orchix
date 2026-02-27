import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def check_sudo():
    '''Ensure running with sudo (Linux only)'''
    import platform
    
    # Skip sudo check on Windows
    if platform.system().lower() == 'windows':
        return
    
    # Linux/Mac: Check sudo
    if os.geteuid() != 0:
        print("⚠️  ORCHIX requires sudo privileges on Linux")
        print("   Restarting with sudo...")
        subprocess.run(["sudo", "python3", __file__])
        sys.exit()


def print_header():
    '''Print ORCHIX startup header with Rich'''

    console = Console()

    logo = Text()
    logo.append("   ___  ____   ____ _   _ _____  __\n", style="bold cyan")
    logo.append("  / _ \\|  _ \\ / ___| | | |_ _\\ \\/ /\n", style="bold cyan")
    logo.append(" | | | | |_) | |   | |_| || | \\  / \n", style="cyan")
    logo.append(" | |_| |  _ <| |___|  _  || | /  \\ \n", style="cyan")
    logo.append("  \\___/|_| \\_\\\\____|_| |_|___/_/\\_\\\n\n", style="dim cyan")
    logo.append("  v1.4", style="bold white")
    logo.append("  |  Container Management System", style="dim")

    panel = Panel(
        logo,
        border_style="cyan",
        padding=(1, 2)
    )

    console.print()
    console.print(panel)
    console.print()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == 'service':
        action = sys.argv[2] if len(sys.argv) > 2 else 'status'
        from cli.service_manager import handle_service_command
        handle_service_command(action)
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == 'init-users':
        from web.auth import ensure_users_exist
        ensure_users_exist()
        sys.exit(0)

    if '--web' in sys.argv:
        # Web UI mode — on Windows, prevent all subprocess calls from opening console windows
        import platform
        if platform.system() == 'Windows':
            _orig_run   = subprocess.run
            _orig_popen = subprocess.Popen
            _NO_WINDOW  = subprocess.CREATE_NO_WINDOW
            def _run_no_window(*a, **kw):
                kw.setdefault('creationflags', _NO_WINDOW)
                return _orig_run(*a, **kw)
            def _popen_no_window(*a, **kw):
                kw.setdefault('creationflags', _NO_WINDOW)
                return _orig_popen(*a, **kw)
            subprocess.run   = _run_no_window
            subprocess.Popen = _popen_no_window

        port = 5000
        for i, arg in enumerate(sys.argv):
            if arg == '--port' and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    pass

        print_header()
        from utils.docker_utils import ensure_orchix_network
        ensure_orchix_network()
        from web.server import run_web
        run_web(port=port)
    else:
        # CLI mode
        check_sudo()
        print_header()
        from utils.docker_utils import ensure_orchix_network
        ensure_orchix_network()
        from cli.main_menu import run_main_loop
        run_main_loop()