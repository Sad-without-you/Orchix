from random import choices
from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning, show_step, show_step_final, show_result_panel, show_step_detail, show_step_line, step_input
from apps.manifest_loader import load_all_manifests
from license import get_license_manager, PRICING
from license.features import get_pro_benefits
from license.audit_logger import get_audit_logger, AuditEventType
import subprocess
from utils.license_check import can_install_app, get_app_badge, show_upgrade_prompt_for_app
from cli.license_menu import _activate_pro_license
from utils.docker_utils import safe_docker_run, get_docker_compose_command
import re
import os

def check_container_exists(container_name):
    '''Check if container already exists'''
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return False
    return container_name in result.stdout.strip()


def is_port_in_use(port):
    '''Check if port is already in use'''
    result = safe_docker_run(
        ['docker', 'ps', '--format', '{{.Ports}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return False
    return f':{port}->' in result.stdout or f'0.0.0.0:{port}' in result.stdout


def find_free_port(start_port=5678, max_attempts=10):
    '''Find next free port starting from start_port'''
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port  # Fallback


def _tag_instance_image(instance_name, compose_file):
    '''Tag Docker image with instance-specific name to isolate instances'''
    if not os.path.exists(compose_file):
        return

    with open(compose_file, 'r') as f:
        content = f.read()

    # Find the image line in compose file
    match = re.search(r'image:\s*(.+)', content)
    if not match:
        return

    original_image = match.group(1).strip()
    instance_image = f"{instance_name}:orchix"

    # Skip if already instance-specific (e.g. lightrag builds its own)
    if instance_name in original_image.split(':')[0].split('/')[-1]:
        return

    # Tag the original image for this instance
    result = safe_docker_run(
        ['docker', 'tag', original_image, instance_image],
        capture_output=True, text=True
    )
    if not result or result.returncode != 0:
        return

    # Update compose file: store original as comment, use instance tag
    new_content = f"# orchix_source_image: {original_image}\n"
    new_content += content.replace(f'image: {original_image}', f'image: {instance_image}')

    with open(compose_file, 'w') as f:
        f.write(new_content)

    # Recreate container with tagged image (fast - same layers)
    docker_compose_cmd = get_docker_compose_command()
    safe_docker_run(
        docker_compose_cmd + ['-f', compose_file, 'up', '-d'],
        capture_output=True, text=True
    )


def show_install_menu():
    '''Install applications menu'''
    
    # ✨ CHECK DOCKER FIRST!
    from utils.system import check_docker, is_windows
    
    docker_status = check_docker()
    
    if not docker_status['installed']:
        show_panel("Install Applications", "Docker Required")
        print()
        show_error("Docker is not installed!")
        print()
        show_info("Docker is required to install applications.")
        print()
        show_info("Please install Docker first:")
        
        if is_windows():
            print("  1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop")
            print("  2. Install and restart your computer")
            print("  3. Start Docker Desktop")
        else:
            print("  1. Run: ORCHIX → System Setup")
            print("  2. Select: Install Docker")
        
        print()
        input("Press Enter to return...")
        return
    
    if not docker_status['running']:
        show_panel("Install Applications", "Docker Not Running")
        print()
        show_error("Docker is not running!")
        print()
        show_info("Please start Docker:")
        
        if is_windows():
            print("  1. Open Docker Desktop")
            print("  2. Wait for Docker to start (green icon in system tray)")
            print("  3. Return to ORCHIX")
        else:
            print("  1. Run: sudo systemctl start docker")
            print("  2. Or: sudo service docker start")
        
        print()
        
        # Check for permission issues
        result = safe_docker_run(
            ['docker', 'ps'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        if result is None:
            show_error("Docker is not installed!")
            print()
            input("Press Enter to return...")
            return

        if result.returncode != 0 and "permission denied" in result.stderr.lower():
            show_warning("Permission issue detected!")
            print()
            if not is_windows():
                print("  Add user to docker group:")
                print("    sudo usermod -aG docker $USER")
                print("    newgrp docker")
                print()
                print("  Or run with sudo:")
                print("    sudo python3 main.py")
        
        print()
        input("Press Enter to return...")
        return
    
    # Docker is ready - proceed with menu
    license_manager = get_license_manager()
    
    # ✨ WHILE LOOP FOR MULTIPLE INSTALLATIONS
    while True:
        container_status = license_manager.check_container_limit()
        
        if container_status['reached'] and license_manager.is_free():
            show_panel("Install Applications", "Container limit reached")
            print()
            show_warning(f"You have reached the FREE tier limit ({container_status['limit']} containers)")
            print()
            show_info("To install more containers, upgrade to PRO:")
            print("  • Unlimited containers")
            print("  • Backup & Restore")
            print("  • Migration tools")
            print()
            show_info(f"Upgrade for only {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}")
            print()
            
            choice = select_from_list(
                "What would you like to do?",
                ["⬆️  Upgrade to PRO", "⬅️  Back to Main Menu"]
            )
            
            if "Upgrade" in choice:
                from cli.license_menu import _activate_pro_license
                _activate_pro_license()
                # Continue loop to refresh after upgrade
                continue
            else:
                # Back to main menu
                return
        
        # Continue with normal installation
        show_panel("Install Applications", "Select application to install")
        
        # Load available apps
        manifests = load_all_manifests()
        
        if not manifests:
            show_error("No application manifests found!")
            input("Press Enter...")
            return
        
        
        # Build choices
        choices = []
        for manifest in manifests.values():
            name = manifest.get('name', manifest['name'])
            display_name = manifest.get('display_name', name)
            icon = manifest.get('icon', '📦')
            
            # Get license badge (dynamic!)
            badge = get_app_badge(manifest)

            # Format download size
            size_mb = manifest.get('image_size_mb', 0)
            if size_mb >= 1000:
                size_str = f" (~{size_mb / 1024:.1f} GB)"
            elif size_mb > 0:
                size_str = f" (~{size_mb} MB)"
            else:
                size_str = ""

            if display_name:
                choices.append(f"{icon} {name} - {display_name}{size_str}{badge}")
            else:
                choices.append(f"{icon} {name}{size_str}{badge}")

        choices.append("⬅️  Back to Main Menu")
        
        # User selects app
        choice = select_from_list("Select application to install", choices)
        
        if "Back to Main Menu" in choice:
            return
        
       # Extract app name from choice
        for app_name, manifest in manifests.items():
            name = manifest.get('name', manifest['name'])
            if name in choice:
                # Check license (dynamic!)
                check_result = can_install_app(manifest)
                
                if not check_result['allowed']:
                    # Show upgrade prompt
                    if check_result['upgrade_required']:
                        show_upgrade_prompt_for_app(manifest)
                    # Return to menu
                    continue
                
                # License OK - install
                install_app(app_name, manifest)
                break


def install_app(app_name, manifest):
    '''Install a specific app'''
    
    # Show download size info
    size_mb = manifest.get('image_size_mb', 0)
    if size_mb >= 1000:
        size_info = f"Download size: ~{size_mb / 1024:.1f} GB"
    elif size_mb > 0:
        size_info = f"Download size: ~{size_mb} MB"
    else:
        size_info = "Setting up container..."

    show_panel(f"Installing {manifest['display_name']}", size_info)

    # Check if default instance exists
    if check_container_exists(app_name):
        show_warning(f"Container '{app_name}' already exists!")
        
        action = select_from_list(
            "What would you like to do?",
            [
                "➕ Create new instance (custom name/port)",
                "⬅️  Cancel"
            ]
        )
        
        if "Cancel" in action:
            return
    
        license_manager = get_license_manager()
            
        if license_manager.is_free():
            show_warning(f"Multi-Instance feature is PRO only!")
            print()
            show_info(f"You already have: {app_name}")
            show_info("FREE tier allows only ONE instance per app")
            print()
            show_info("Upgrade to PRO to unlock:")
            print("  • Multiple instances per app")
            print("  • Unlimited containers")
            print("  • Backup & Restore")
            print()
            show_info(f"Price: {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}")
            print()

            choice = select_from_list(
                "What would you like to do?",
                ["⬆️  Upgrade to PRO", "⬅️  Cancel Installation"]
            )
            
            if "Upgrade" in choice:
                from cli.license_menu import _activate_pro_license
                _activate_pro_license()
            
            return

    # Get instance details
    show_step_detail(f"Configuring {manifest['display_name']} instance")

    # Instance name - app name is always the prefix, user can only add a suffix
    show_step_detail(f"Container name: {app_name}<suffix>")
    show_step_detail(f"Examples: {app_name}, {app_name}2, {app_name}-dev, {app_name}_prod")
    suffix = step_input(f"Suffix (leave empty for '{app_name}'): ").strip()

    if suffix:
        # Only allow suffixes starting with digit, dash or underscore
        if not suffix[0].isdigit() and suffix[0] not in ('-', '_'):
            suffix = '-' + suffix
        instance_name = f"{app_name}{suffix}"
    else:
        instance_name = app_name

    # Check if THIS instance exists
    if check_container_exists(instance_name):
        show_error(f"Instance '{instance_name}' already exists!")
        input("Press Enter...")
        return

    # Get installer class
    InstallerClass = manifest.get('installer_class')
    
    if not InstallerClass:
        show_error(f"No installer available for {app_name}")
        input("Press Enter...")
        return
    
    # Create installer instance
    installer = InstallerClass(manifest)
    
    # Check dependencies
    show_step("Checking dependencies...", "active")
    if not installer.check_dependencies():
        show_step("Required dependencies not available!", "error")
        show_info(f"Required: {manifest['requires']['system']}")
        input("Press Enter...")
        return

    show_step("Dependencies OK")

    # Get base configuration
    show_step_line()
    config = installer.get_configuration(instance_name)
    
    if config is None:
        show_info("Configuration cancelled")
        input("Press Enter...")
        return
    
    # Smart port selection - SKIP if app configured its own ports
    if 'skip_port_config' not in config and 'http_port' not in config:
        default_port = config.get('port', 5678)
        
        # If creating new instance, find free port
        if instance_name != app_name:
            default_port = find_free_port(default_port)
            show_step_detail(f"Suggested free port: {default_port}")

        custom_port = step_input(f"Port (default: {default_port}): ").strip()
        if custom_port:
            try:
                config['port'] = int(custom_port)
            except ValueError:
                show_step_detail(f"Invalid port, using: {default_port}")
                config['port'] = default_port
        else:
            config['port'] = default_port
    # else: Ports already configured by installer (e.g., Nginx Proxy Manager)
    
    # Add instance-specific config
    config['instance_name'] = instance_name
    config['volume_name'] = f"{instance_name}_data"
    
    show_step("Configuration ready")

    # Install
    show_step(f"Installing {manifest['display_name']} as '{instance_name}'...", "active")
    success = installer.install(config, instance_name)
    
    if success:
        # Tag image with instance-specific name for safe uninstall
        compose_file = f"docker-compose-{instance_name}.yml"
        _tag_instance_image(instance_name, compose_file)

        show_step_final(f"{manifest['display_name']} installed successfully!", True)

        # Log audit event for PRO users
        license_manager = get_license_manager()
        audit_logger = get_audit_logger(enabled=license_manager.is_pro())
        audit_logger.log_event(
            AuditEventType.INSTALL,
            app_name,
            {
                'instance_name': instance_name,
                'version': manifest.get('version', 'unknown'),
                'port': config.get('port', 'N/A'),
                'status': 'success'
            }
        )
        
        # Get success message from hook or generate access info
        from apps.hook_loader import get_hook_loader
        hook_loader = get_hook_loader()

        if hook_loader.has_hook(manifest, 'success_message'):
            message = hook_loader.execute_hook(manifest, 'success_message', config)
            if message:
                show_result_panel(message.strip(), f"{manifest['display_name']} Ready")
        else:
            message = _build_access_message(manifest, config, instance_name)
            show_result_panel(message, f"{manifest['display_name']} Ready")
    else:
        show_step_final("Installation failed!", False)
        
        # Log failure for PRO users
        license_manager = get_license_manager()
        audit_logger = get_audit_logger(enabled=license_manager.is_pro())
        audit_logger.log_event(
            AuditEventType.INSTALL,
            app_name,
            {
                'instance_name': instance_name,
                'version': manifest.get('version', 'unknown'),
                'port': config.get('port', 'N/A'),
                'status': 'failed'
            }
        )
    
    input("\nPress Enter...")


def _build_access_message(manifest, config, instance_name):
    """Auto-detect access info from template data. No hardcoding needed."""
    port = config.get('port', '')
    template = manifest.get('_template', {})
    ports = template.get('ports', [])
    envs = template.get('env', [])
    image = template.get('image', manifest.get('image', ''))
    lines = []

    # Detect access type from port labels
    web_keywords = {'web ui', 'http', 'https', 'dashboard', 'admin', 'console'}
    has_web = any(
        any(kw in p.get('label', '').lower() for kw in web_keywords)
        for p in ports
    )

    if not ports:
        lines.append('Runs in background (no access needed)')
    elif has_web:
        lines.append(f'Access at: http://localhost:{port}')
    else:
        # CLI service - detect tool from image name
        cli_cmd = _detect_cli_command(image, config, instance_name)
        if cli_cmd:
            lines.append(f'CLI:  {cli_cmd}')
        lines.append(f'Host: localhost:{port}')

    # Auto-detect credentials from env vars with type=password or generate=true
    creds = []
    for env in envs:
        val = config.get(env['key'])
        if val and (env.get('type') == 'password' or env.get('generate')):
            creds.append((env.get('label', env['key']), val))
        elif val and env.get('key', '').upper().endswith(('_USER', '_USERNAME')):
            creds.append((env.get('label', env['key']), val))
    if creds:
        lines.append('')
        for label, val in creds:
            lines.append(f'{label}: {val}')

    return '\n'.join(lines)


# Image name → CLI tool mapping (extensible)
_CLI_TOOLS = {
    'redis': 'redis-cli',
    'postgres': lambda c: f'psql -U {c.get("POSTGRES_USER", "postgres")}',
    'mariadb': 'mysql -u root -p',
    'mysql': 'mysql -u root -p',
    'mongo': 'mongosh',
    'mosquitto': 'mosquitto_sub -t "#"',
    'memcached': 'sh -c "echo stats | nc localhost 11211"',
}


def _detect_cli_command(image, config, instance_name):
    """Detect CLI command from Docker image name."""
    image_lower = image.lower()
    for key, cmd in _CLI_TOOLS.items():
        if key in image_lower:
            tool = cmd(config) if callable(cmd) else cmd
            return f'docker exec -it {instance_name} {tool}'
    return None