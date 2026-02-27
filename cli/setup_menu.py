# ORCHIX v1.4
from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning
from utils.system import (
    detect_os, detect_package_manager, check_docker, check_dependencies,
    check_wsl2, is_windows, is_linux,
    install_docker_linux, install_docker_windows, install_wsl2,
    start_docker, install_basic_tools
)
from rich.console import Console
from rich.table import Table

console = Console()


def show_setup_menu():
    '''System setup and requirements menu'''
    
    while True:
        show_panel("System Setup", "Check and install system requirements")
        
        choices = [
            "🔍 Check System Requirements",
            "🐳 Install Docker",
            "📦 Install Dependencies",
            "✅ Verify Installation",
            "🔄 Check for ORCHIX Updates",
            "⬅️  Back to Main Menu"
        ]
        
        # Add WSL2 option for Windows
        if is_windows():
            choices.insert(2, "🪟 Install WSL2")
        
        choice = select_from_list("Select action", choices)
        
        if choice == "⬅️  Back to Main Menu":
            break
        
        if "Check System" in choice:
            check_system_requirements()
        elif "Install Docker" in choice:
            install_docker_menu()
        elif "Install WSL2" in choice and is_windows():
            install_wsl2_menu()
        elif "Install Dependencies" in choice:
            install_dependencies_menu()
        elif "Verify" in choice:
            verify_installation()
        elif "ORCHIX Updates" in choice:
            check_orchix_updates()


def check_system_requirements():
    '''Check and display system requirements'''
    
    console = Console()
    
    show_info("Checking system requirements...")
    print()
    
    # Detect system
    os_type = detect_os()
    pkg_manager = detect_package_manager()
    docker_status = check_docker()
    deps = check_dependencies()
    
    # Create system info table
    table = Table(title="💻 System Information", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Status", style="white", width=50)
    
    # OS
    table.add_row("Operating System", f"✅ {os_type.upper()}")
    
    # Package Manager
    if pkg_manager:
        table.add_row("Package Manager", f"✅ {pkg_manager}")
    else:
        table.add_row("Package Manager", "❌ Not detected")
    
    # WSL2 (Windows only)
    if is_windows():
        wsl2_status = check_wsl2()
        if wsl2_status['installed']:
            table.add_row("WSL2", f"✅ Installed (Version {wsl2_status['version']})")
        else:
            table.add_row("WSL2", "❌ Not installed (Required for Docker)")
    
    console.print()
    console.print(table)
    console.print()
    
    # Create requirements table
    req_table = Table(title="📋 Requirements Status", show_header=True, header_style="bold cyan")
    req_table.add_column("Requirement", style="cyan", width=25)
    req_table.add_column("Status", style="white", width=50)
    
    # Docker
    if docker_status['installed']:
        if docker_status['running']:
            req_table.add_row("Docker", "✅ Installed and running")
        else:
            req_table.add_row("Docker", "⚠️  Installed but not running")
    else:
        req_table.add_row("Docker", "❌ Not installed")
    
    # Docker Desktop (Windows)
    if is_windows():
        if docker_status.get('desktop'):
            req_table.add_row("Docker Desktop", "✅ Running")
        else:
            req_table.add_row("Docker Desktop", "❌ Not running")
    
    # Dependencies
    if is_linux():
        curl_status = "✅ Installed" if deps.get('curl') else "❌ Not installed"
        wget_status = "✅ Installed" if deps.get('wget') else "❌ Not installed"
        
        req_table.add_row("curl", curl_status)
        req_table.add_row("wget", wget_status)
    
    console.print(req_table)
    console.print()
    
    # Summary
    if docker_status['installed'] and docker_status['running']:
        show_success("System is ready for ORCHIX!")
    else:
        show_warning("Some requirements are missing")
        show_info("Use the Setup menu to install missing components")
    
    print()
    input("Press Enter...")


def install_docker_menu():
    '''Install Docker'''
    
    show_panel("Install Docker", "Docker installation wizard")
    
    # Check if already installed
    docker_status = check_docker()
    
    if docker_status['installed']:
        show_warning("Docker is already installed!")

        if not docker_status['running']:
            show_info("Docker is not running. Would you like to start it?")

            choice = select_from_list(
                "Start Docker?",
                ["✅ Yes, start Docker", "⬅️  Cancel"]
            )

            if "Yes" in choice:
                start_docker()
        else:
            show_success("Docker is running!")

        print()

        # Give user options instead of returning immediately
        choice = select_from_list(
            "What would you like to do?",
            [
                "🔄 Reinstall Docker (overwdites existing installation)",
                "ℹ️  Show Docker Info",
                "⬅️  Back todMenu"
            ]
        )

        if "Reinstall" in choice:
            show_warning("This will reinstall Docker. Existing containers will be preserved.")
            confirm = select_from_list(
                "Are you sure?",
                ["✅ Yes, reinstall", "❌ Cancel"]
            )
            if "Cancel" in confirm:
                return
            # Continue with installation below
        elif "Show Docker Info" in choice:
            show_info("Docker Information:")
            print()

            # Create a nice table for Docker info
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Property", style="cyan", width=20)
            table.add_column("Status", style="bold")

            # Add rows with status symbols
            installed_status = "✅ Yes" if docker_status['installed'] else "❌ No"
            running_status = "✅ Yes" if docker_status['running'] else "❌ No"

            table.add_row("Installed", installed_status)
            table.add_row("Running", running_status)

            # Print version info if available
            if docker_status.get('version'):
                table.add_row("Version", docker_status['version'])

            console.print(table)
            print()
            input("Press Enter to continue...")
            return
        else:
            return
    
    # Detect OS and package manager
    os_type = detect_os()
    pkg_manager = detect_package_manager()
    
    show_info(f"Detected: {os_type.upper()}")
    print()
    
    # Platform-specific installation
    if is_windows():
        # Check WSL2
        wsl2_status = check_wsl2()
        if not wsl2_status['installed']:
            show_error("WSL2 is required for Docker Desktop!")
            show_info("Please install WSL2 first (option: 🪟 Install WSL2)")
            input("\nPress Enter...")
            return
        
        show_warning("This will install Docker Desktop for Windows")
        show_info("Requirements:")
        show_info("  • Windows 10/11 (64-bit)")
        show_info("  • WSL2 (installed ✅)")
        show_info("  • 4GB RAM minimum")
        show_info("  • Administrator privileges")
        show_info("  • System restart required")
        print()
        
        confirm = select_from_list(
            "Continue with installation?",
            ["✅ Yes, install Docker Desktop", "⬅️  Cancel"]
        )
        
        if "Yes" in confirm:
            success = install_docker_windows()
            if success:
                show_info("Please restart your computer and start ORCHIX again")
        
    elif is_linux():
        if not pkg_manager:
            show_error("No supported package manager found!")
            input("\nPress Enter...")
            return
        
        show_warning(f"This will install Docker using {pkg_manager}")
        show_info("Requirements:")
        show_info("  • Ubuntu/Debian 64-bit")
        show_info("  • Internet connection")
        show_info("  • Root/sudo privileges")
        print()
        
        confirm = select_from_list(
            "Continue with installation?",
            ["✅ Yes, install Docker", "⬅️  Cancel"]
        )
        
        if "Yes" in confirm:
            success = install_docker_linux(os_type, pkg_manager)
            
            if success:
                # Start Docker
                show_info("Starting Docker service...")
                start_docker()
                
                # Add user to docker group
                import os
                username = os.environ.get('SUDO_USER', os.environ.get('USER'))
                if username:
                    show_info(f"Adding {username} to docker group...")
                    import subprocess
                    subprocess.run(['usermod', '-aG', 'docker', username], capture_output=True)
                    show_info("Please log out and back in for group changes to take effect")
    
    else:
        show_error("Unsupported operating system")
    
    print()
    input("Press Enter...")


def install_wsl2_menu():
    '''Install WSL2 (Windows only)'''
    
    if not is_windows():
        show_error("WSL2 is only for Windows!")
        input("Press Enter...")
        return
    
    show_panel("Install WSL2", "Windows Subsystem for Linux 2")
    
    # Check if already installed
    wsl2_status = check_wsl2()
    
    if wsl2_status['installed']:
        show_success(f"WSL2 is already installed (Version {wsl2_status['version']})")
        input("\nPress Enter...")
        return
    
    show_info("WSL2 enables Linux containers on Windows")
    show_info("Required for Docker Desktop")
    print()
    
    show_warning("This installation will:")
    show_info("  • Enable Windows features (Hyper-V, WSL)")
    show_info("  • Download Ubuntu Linux")
    show_info("  • Require system restart")
    print()
    
    confirm = select_from_list(
        "Continue with installation?",
        ["✅ Yes, install WSL2", "⬅️  Cancel"]
    )
    
    if "Yes" in confirm:
        success = install_wsl2()
        
        if success:
            show_info("Please restart your computer to complete installation")
    
    print()
    input("Press Enter...")


def install_dependencies_menu():
    '''Install basic dependencies'''
    
    show_panel("Install Dependencies", "Install required tools")
    
    if is_windows():
        show_info("Windows 10+ includes curl by default")
        show_success("No additional dependencies needed!")
        input("\nPress Enter...")
        return
    
    # Linux dependencies
    deps = check_dependencies()
    
    if deps.get('curl') and deps.get('wget'):
        show_success("All dependencies are already installed!")
        input("\nPress Enter...")
        return
    
    pkg_manager = detect_package_manager()
    
    if not pkg_manager:
        show_error("No supported package manager found!")
        input("\nPress Enter...")
        return
    
    show_info("This will install:")
    show_info("  • curl - Data transfer tool")
    show_info("  • wget - File downloader")
    show_info("  • ca-certificates - SSL certificates")
    print()
    
    confirm = select_from_list(
        "Continue with installation?",
        ["✅ Yes, install dependencies", "⬅️  Cancel"]
    )
    
    if "Yes" in confirm:
        install_basic_tools(pkg_manager)
    
    print()
    input("Press Enter...")


def check_orchix_updates():
    '''Check for ORCHIX updates from GitHub'''

    show_panel("ORCHIX Update Check", "Checking for new versions...")
    print()

    try:
        from utils.version_check import check_for_updates, CURRENT_VERSION

        show_info(f"Current version: v{CURRENT_VERSION}")
        show_info("Checking GitHub for updates...")
        print()

        result = check_for_updates()

        if result is None:
            show_error("Could not reach GitHub. Check your internet connection.")
        elif result['update_available']:
            show_warning(f"New version available: v{result['latest_version']}")
            print()

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("", style="cyan", width=20)
            table.add_column("", style="white", width=30)
            table.add_row("Current Version", f"v{CURRENT_VERSION}")
            table.add_row("Latest Version", f"v{result['latest_version']}")
            console.print(table)
            print()

            show_info("To update, run these commands:")
            print("  cd /path/to/ORCHIX")
            print("  git pull")
            print("  pip install -r requirements.txt")
            print()

            choice = select_from_list(
                "Would you like to update now?",
                ["🔄 Update now (git pull)", "⬅️  Later"]
            )

            if "Update now" in choice:
                _run_update()
                return
        else:
            show_success(f"You are up to date! (v{CURRENT_VERSION})")
    except Exception as e:
        show_error(f"Update check failed: {e}")

    print()
    input("Press Enter...")


def _run_update():
    '''Run git pull to update ORCHIX'''
    import subprocess
    import os

    show_info("Updating ORCHIX...")
    print()

    orchix_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        # Git pull
        result = subprocess.run(
            ['git', 'pull'],
            cwd=orchix_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )

        if result.returncode == 0:
            print(result.stdout)
            show_success("Git pull completed!")
            print()

            # Install updated dependencies
            show_info("Updating dependencies...")
            pip_result = subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt'],
                cwd=orchix_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=120
            )

            if pip_result.returncode == 0:
                show_success("Dependencies updated!")
            else:
                show_warning("Dependency update had issues:")
                print(pip_result.stderr[:500] if pip_result.stderr else "")

            print()
            show_warning("Please restart ORCHIX to apply updates.")
        else:
            show_error("Git pull failed:")
            print(result.stderr[:500] if result.stderr else "Unknown error")

    except subprocess.TimeoutExpired:
        show_error("Update timed out. Check your internet connection.")
    except FileNotFoundError:
        show_error("Git not found. Please install git or update manually.")
    except Exception as e:
        show_error(f"Update failed: {e}")

    print()
    input("Press Enter...")


def verify_installation():
    '''Verify complete installation'''
    
    console = Console()
    
    show_info("Verifying installation...")
    print()
    
    docker_status = check_docker()
    deps = check_dependencies()
    
    # Create verification table
    table = Table(title="✅ Installation Verification", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Status", style="white", width=50)
    
    # Docker installed
    if docker_status['installed']:
        table.add_row("Docker Installed", "✅ Yes")
    else:
        table.add_row("Docker Installed", "❌ No - Install via Setup menu")
    
    # Docker running
    if docker_status['running']:
        table.add_row("Docker Running", "✅ Yes")
    else:
        table.add_row("Docker Running", "❌ No - Start Docker service")
    
    # Platform-specific checks
    if is_windows():
        wsl2_status = check_wsl2()
        if wsl2_status['installed']:
            table.add_row("WSL2", "✅ Installed")
        else:
            table.add_row("WSL2", "❌ Not installed")
        
        if docker_status.get('desktop'):
            table.add_row("Docker Desktop", "✅ Running")
        else:
            table.add_row("Docker Desktop", "❌ Not running")
    
    elif is_linux():
        if deps.get('curl'):
            table.add_row("curl", "✅ Installed")
        else:
            table.add_row("curl", "❌ Not installed")
        
        if deps.get('wget'):
            table.add_row("wget", "✅ Installed")
        else:
            table.add_row("wget", "❌ Not installed")
    
    console.print()
    console.print(table)
    console.print()
    
    # Final verdict
    if docker_status['installed'] and docker_status['running']:
        show_success("  ORCHIX is ready to use!")
        show_info("You can now install applications from the main menu")
    else:
        show_warning("Setup incomplete")
        show_info("Please complete the installation steps in the Setup menu")
    
    print()
    input("Press Enter...")