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
    '''Print ORCHIX header with Rich'''

    
    console = Console()
    
    # Create title
    title = Text()
    title.append("ORCHIX v1.1\n", style="bold cyan")
    title.append("DevOps Container Management System", style="dim")
    
    # Show panel
    panel = Panel(
        title,
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print()
    console.print(panel)
    console.print()


if __name__ == "__main__":
    # Check sudo
    check_sudo()

    # Run main loop
    from cli.main_menu import run_main_loop
    run_main_loop()