# ORCHIX v1.1
import subprocess
import os
import sys
import platform
from cli.ui import show_info, show_success, show_error, show_warning


def get_platform():
    '''Detect platform (linux/windows/darwin)'''
    return platform.system().lower()


def is_windows():
    '''Check if running on Windows'''
    return get_platform() == 'windows'


def is_linux():
    '''Check if running on Linux'''
    return get_platform() == 'linux'


def detect_os():
    '''Detect operating system details'''
    
    if is_windows():
        try:
            import sys
            if hasattr(sys, 'getwindowsversion'):
                win_ver = sys.getwindowsversion()
                
                # Windows 11 check
                if win_ver.major == 10 and win_ver.build >= 22000:
                    return 'windows11'
                elif win_ver.major == 10:
                    return 'windows10'
                elif win_ver.major == 11:
                    return 'windows11'
            
            # Fallback
            version = platform.version()
            parts = version.split('.')
            if len(parts) >= 3:
                build = int(parts[2])
                if build >= 22000:
                    return 'windows11'
                else:
                    return 'windows10'
        except:
            pass
        
        return 'windows'
    
    elif is_linux():
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                
                if 'ubuntu' in content:
                    return 'ubuntu'
                elif 'debian' in content:
                    return 'debian'
                elif 'arch' in content:
                    return 'arch'
                elif 'fedora' in content:
                    return 'fedora'
                else:
                    return 'linux'
        except:
            return 'linux'
    
    else:
        return 'unknown'


def detect_package_manager():
    '''Detect available package manager'''
    
    if is_windows():
        # Check for winget (Windows Package Manager)
        if check_command_exists('winget'):
            return 'winget'
        # Check for chocolatey
        elif check_command_exists('choco'):
            return 'choco'
        else:
            return None
    
    else:
        # Linux package managers
        managers = {
            'apt': ['apt-get', '--version'],
            'yum': ['yum', '--version'],
            'dnf': ['dnf', '--version'],
            'pacman': ['pacman', '--version']
        }
        
        for manager, cmd in managers.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return manager
            except:
                continue
        
        return None


def check_command_exists(command):
    '''Check if command exists (cross-platform)'''
    
    try:
        if is_windows():
            # Windows: use 'where' command
            result = subprocess.run(
                ['where', command],
                capture_output=True,
                text=True,
                encoding='utf-8',  # ← ADD
                errors='ignore',   # ← ADD
                shell=False
            )
            return result.returncode == 0
        else:
            # Linux/Mac: use 'which' command
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True,
                encoding='utf-8',  # ← ADD
                errors='ignore'    # ← ADD
            )
            return result.returncode == 0
    except Exception:
        return False


def check_docker():
    '''Check if Docker is installed and running (cross-platform)'''
    
    # Check if installed
    if not check_command_exists('docker'):
        return {'installed': False, 'running': False, 'desktop': False}
    
    # Check if running
    try:
        result = subprocess.run(
            ['docker', 'version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        running = result.returncode == 0
    except Exception:
        running = False
    
    # Check if Docker Desktop (Windows)
    desktop = False
    if is_windows():
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq Docker Desktop.exe'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                shell=False
            )
            if result.stdout:  # Check not None
                desktop = 'Docker Desktop.exe' in result.stdout
        except Exception:
            desktop = False
    
    return {
        'installed': True,
        'running': running,
        'desktop': desktop
    }


def check_wsl2():
    '''Check if WSL2 is installed (Windows only)'''
    
    if not is_windows():
        return {'installed': True, 'version': 2}
    
    try:
        result = subprocess.run(
            ['wsl', '--status'],
            capture_output=True,
            text=True,
            encoding='utf-8',  # ← ADD
            errors='ignore',   # ← ADD
            shell=False
        )
        
        if result.returncode == 0 and result.stdout:  # ← ADD None check
            # Check version
            if 'version: 2' in result.stdout.lower() or 'version 2' in result.stdout.lower():
                return {'installed': True, 'version': 2}
            else:
                return {'installed': True, 'version': 1}
        else:
            return {'installed': False, 'version': None}
    except Exception:
        return {'installed': False, 'version': None}


def check_dependencies():
    '''Check all required dependencies (cross-platform)'''
    
    deps = {
        'docker': check_docker()['installed'],
        'docker_running': check_docker()['running']
    }
    
    if is_windows():
        deps['wsl2'] = check_wsl2()['installed']
        deps['docker_desktop'] = check_docker()['desktop']
    else:
        deps['curl'] = check_command_exists('curl')
        deps['wget'] = check_command_exists('wget')
    
    return deps


def install_docker_linux(os_type, pkg_manager):
    '''Install Docker on Linux using official script'''
    
    show_info("Installing Docker using official script...")
    print()
    
    # Check if curl exists
    if not check_command_exists('curl'):
        show_info("Installing curl first...")
        
        if pkg_manager == 'apt':
            subprocess.run(['apt-get', 'update'], capture_output=True)
            result = subprocess.run(['apt-get', 'install', '-y', 'curl'], capture_output=True, text=True)
        elif pkg_manager in ['yum', 'dnf']:
            result = subprocess.run([pkg_manager, 'install', '-y', 'curl'], capture_output=True, text=True)
        elif pkg_manager == 'pacman':
            result = subprocess.run(['pacman', '-S', '--noconfirm', 'curl'], capture_output=True, text=True)
        else:
            show_error("Cannot install curl - no package manager")
            return False
        
        if result.returncode != 0:
            show_error("Failed to install curl")
            return False
    
    # Use official Docker install script
    from utils.docker_progress import run_command_with_progress

    # Note: shell=True required for pipe operation (curl | sh)
    # URL is hardcoded (get.docker.com) so no injection risk
    result = run_command_with_progress(
        'curl -fsSL https://get.docker.com | sh',
        "Downloading and installing Docker (this may take a few minutes)",
        shell=True
    )
    
    if result.returncode == 0:
        show_success("Docker installed successfully!")
        
        # Show output
        if result.stdout:
            print("\nInstallation output:")
            print(result.stdout[-500:])  # Last 500 chars
        
        return True
    else:
        show_error("Docker installation failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return False


def install_docker_windows():
    '''Install Docker Desktop on Windows'''
    
    show_info("Installing Docker Desktop for Windows...")
    print()
    
    # Check WSL2 first
    wsl2_status = check_wsl2()
    if not wsl2_status['installed']:
        show_error("WSL2 is required for Docker Desktop!")
        show_info("Please install WSL2 first using the Setup menu")
        return False
    
    # Download Docker Desktop installer
    from utils.docker_progress import run_command_with_progress

    installer_url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    installer_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'DockerDesktopInstaller.exe')

    # Download using PowerShell
    ps_cmd = f'''
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "{installer_url}" -OutFile "{installer_path}"
    '''

    result = run_command_with_progress(
        ['powershell', '-Command', ps_cmd],
        "Downloading Docker Desktop installer (~500MB)"
    )
    
    if result.returncode != 0:
        show_error(f"Download failed: {result.stderr}")
        return False
    
    # Run installer
    show_info("Running Docker Desktop installer...")
    show_warning("This will require Administrator privileges and a system restart!")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    result = subprocess.run(
        [installer_path, 'install', '--quiet'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        show_success("Docker Desktop installed!")
        show_warning("⚠️  Please restart your computer to complete installation")
        return True
    else:
        show_error("Installation failed")
        return False


def install_wsl2():
    '''Install WSL2 on Windows'''
    from utils.docker_progress import run_command_with_progress

    show_info("Installing WSL2...")
    print()

    # Install WSL (this downloads and installs a Linux distribution)
    result = run_command_with_progress(
        ['wsl', '--install'],
        "Installing WSL2 and Ubuntu (this may take several minutes)",
        shell=False
    )
    
    if result.returncode == 0:
        show_success("WSL2 installed!")
        show_warning("⚠️  Please restart your computer to complete installation")
        return True
    else:
        show_error(f"Installation failed: {result.stderr}")
        return False


def start_docker():
    '''Start Docker service (cross-platform)'''
    
    show_info("Starting Docker...")
    
    if is_windows():
        # Start Docker Desktop
        docker_desktop_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        
        if os.path.exists(docker_desktop_path):
            subprocess.Popen([docker_desktop_path], shell=False)
            show_success("Docker Desktop starting...")
            show_info("Please wait 30-60 seconds for Docker to fully start")
            return True
        else:
            show_error("Docker Desktop not found")
            return False
    
    else:
        # Linux: systemd service
        result = subprocess.run(['systemctl', 'start', 'docker'], capture_output=True, text=True)
        
        if result.returncode == 0:
            subprocess.run(['systemctl', 'enable', 'docker'], capture_output=True)
            show_success("Docker service started!")
            return True
        else:
            show_error("Failed to start Docker")
            return False


def install_basic_tools(pkg_manager):
    '''Install curl, wget (Linux only)'''
    
    if is_windows():
        show_info("Basic tools (curl) are included in Windows 10+")
        return True
    
    show_info("Installing basic tools...")
    
    if pkg_manager == 'apt':
        cmd = ['apt-get', 'install', '-y', 'curl', 'wget', 'ca-certificates']
    elif pkg_manager in ['yum', 'dnf']:
        cmd = [pkg_manager, 'install', '-y', 'curl', 'wget', 'ca-certificates']
    elif pkg_manager == 'pacman':
        cmd = ['pacman', '-S', '--noconfirm', 'curl', 'wget', 'ca-certificates']
    else:
        show_error("Unsupported package manager")
        return False
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        show_success("Basic tools installed!")
        return True
    else:
        show_error("Installation failed")
        return False