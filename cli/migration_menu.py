import subprocess
import tarfile
import json
import os
from pathlib import Path
from datetime import datetime
from cli.ui import show_panel, select_from_list, show_info, show_success, show_error, show_warning
from license import PRICING
from utils.system import is_windows
import shutil
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

# Migration directory
MIGRATION_DIR = Path('migrations')
MIGRATION_DIR.mkdir(exist_ok=True)

BACKUP_DIR = Path('backups')


def show_migration_menu():
    '''Migration management menu'''
    
    from license import get_license_manager
    
    license_manager = get_license_manager()
    
    # PRO Feature Gate
    if license_manager.is_free():
        show_panel("Migration Manager", "⭐ PRO Feature")
        print()
        show_warning("Migration is a PRO feature!")
        print()
        show_info("Upgrade to PRO to unlock:")
        print("  • Export migration packages")
        print("  • Import from other servers")
        print("  • Complete server migration")
        print("  • Backup + Compose files in one package")
        print()
        
        show_info(f"Price: {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}")
        print()
        
        choice = select_from_list(
            "What would you like to do?",
            ["⬆️  Upgrade to PRO", "⬅️  Back to Main Menu"]
        )
        
        if "Upgrade" in choice:
            from cli.license_menu import _activate_pro_license
            _activate_pro_license()
        
        return
    
    # PRO User - Show menu
    while True:
        show_panel("Migration Manager", "PRO Feature - Server Migration")
        
        choices = [
            "📤 Export Migration Package",
            "📥 Import Migration Package",
            "📋 List Migration Packages",
            "ℹ️  Migration Guide",
            "⬅️  Back to Main Menu"
        ]
        
        choice = select_from_list("Select action", choices)
        
        if "Export" in choice:
            export_migration_package()
        
        elif "Import" in choice:
            import_migration_package()
        
        elif "List" in choice:
            list_migration_packages()
        
        elif "Guide" in choice:
            show_migration_guide()
        
        elif "Back" in choice:
            break


def get_all_orchix_containers():
    '''Get all running ORCHIX-managed containers'''

    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []
    
    containers = [c for c in result.stdout.split('\n') if c]
    
    # Filter ORCHIX containers (those with compose files)
    orchix_containers = []
    for container in containers:
        compose_file = Path(f'docker-compose-{container}.yml')
        if compose_file.exists():
            orchix_containers.append(container)
    
    return orchix_containers


def export_migration_package():
    '''Export migration package'''
    
    show_panel("Export Migration Package", "Create migration package")
    
    # Get all containers
    containers = get_all_orchix_containers()
    
    if not containers:
        show_warning("No ORCHIX containers found!")
        input("\nPress Enter...")
        return
    
    print()
    show_info(f"Found {len(containers)} container(s)")
    print()
    
    # Step 1: Ask if select all or pick specific
    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()
    
    # Show available containers
    for container in containers:
        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name)
        icon = manifest.get('icon', '📦') if manifest else '📦'
        print(f"  {icon} {container}")
    
    print()
    
    selection_mode = select_from_list(
        "Selection mode",
        [
            "✅ Export All Containers",
            "🎯 Select Specific Containers",
            "❌ Cancel"
        ]
    )
    
    if "Cancel" in selection_mode:
        show_info("Export cancelled")
        input("\nPress Enter...")
        return
    
    # Handle selection
    if "Export All" in selection_mode:
        selected_containers = containers.copy()
        
    else:  # Select Specific
        print()
        show_info("Select containers (Space to toggle, Enter to confirm)")
        print()
        
        # Build choices with icons
        choices = []
        container_map = {}
        
        for container in containers:
            base_name = container.split('_')[0] if '_' in container else container
            manifest = manifests.get(base_name)
            
            if manifest:
                icon = manifest.get('icon', '📦')
                choice_text = f"{icon} {container}"
            else:
                choice_text = f"📦 {container}"
            
            choices.append(choice_text)
            container_map[choice_text] = container
        
        # Multi-select with checkboxes (all pre-selected)
        import inquirer
        
        questions = [
            inquirer.Checkbox(
                'containers',
                message="Select containers to export",
                choices=choices,
                default=choices  # ALL PRE-SELECTED!
            )
        ]
        
        answers = inquirer.prompt(questions)
        
        if not answers or not answers['containers']:
            show_info("No containers selected - cancelled")
            input("\nPress Enter...")
            return
        
        # Extract container names
        selected_containers = []
        for choice in answers['containers']:
            if choice in container_map:
                selected_containers.append(container_map[choice])
        
        if not selected_containers:
            show_error("No containers selected!")
            input("\nPress Enter...")
            return
    
    # Show selection
    print()
    show_success(f"✅ Selected {len(selected_containers)} container(s):")
    for container in selected_containers:
        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name)
        icon = manifest.get('icon', '📦') if manifest else '📦'
        print(f"   {icon} {container}")
    print()
    
    # ✨ NEW: Select target platform
    target_platform = select_from_list(
        "Target server platform",
        [
            "🐧 Linux (tar.gz backups)",
            "🪟 Windows (zip backups)",
            "❌ Cancel"
        ]
    )
    
    if "Cancel" in target_platform:
        show_info("Export cancelled")
        input("\nPress Enter...")
        return
    
    # Determine target is Windows
    target_is_windows = "Windows" in target_platform
    
    print()
    show_info(f"Target platform: {'Windows (.zip)' if target_is_windows else 'Linux (.tar.gz)'}")
    print()
    
    # Confirm
    confirm = select_from_list(
        "Proceed with export?",
        ["✅ Yes, create package", "❌ Cancel"]
    )
    
    if "Cancel" in confirm:
        show_info("Export cancelled")
        input("\nPress Enter...")
        return
    
    print()

    # Create migration package
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"orchix_migration_{timestamp}"
    package_dir = MIGRATION_DIR / package_name
    package_dir.mkdir(exist_ok=True)

    migration_data = {
        'version': '2.0.0',
        'timestamp': timestamp,
        'source_hostname': _get_hostname(),
        'target_platform': 'windows' if target_is_windows else 'linux',
        'containers': []
    }

    # Process each container with progress bar
    total = len(selected_containers)

    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        main_task = progress.add_task("Creating migration package...", total=total * 100)

        for idx, container in enumerate(selected_containers):
            progress.update(main_task, completed=idx * 100 + 10, description=f"Processing {container}...")

            container_data = {
                'name': container,
                'compose_file': f'docker-compose-{container}.yml',
                'backup_file': None
            }

            # Copy compose file
            progress.update(main_task, completed=idx * 100 + 30, description=f"Copying {container} files...")
            compose_src = Path(f'docker-compose-{container}.yml')
            if compose_src.exists():
                compose_dst = package_dir / compose_src.name
                shutil.copy2(compose_src, compose_dst)

            # Create backup with target platform
            progress.update(main_task, completed=idx * 100 + 50, description=f"Backing up {container}...")
            backup_created = _create_container_backup(container, package_dir, target_is_windows)

            if backup_created:
                container_data['backup_file'] = backup_created

            migration_data['containers'].append(container_data)
            progress.update(main_task, completed=(idx + 1) * 100, description=f"✅ {idx + 1}/{total} processed")

    print()

    # Write manifest with UTF-8
    show_info("Finalizing package...")
    manifest_file = package_dir / 'migration_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(migration_data, f, indent=2)

    # Write README with UTF-8
    readme_file = package_dir / 'README.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"""ORCHIX Migration Package
========================

Created: {timestamp}
Source: {migration_data['source_hostname']}
Target Platform: {migration_data['target_platform'].upper()}
Containers: {len(selected_containers)}

Contents:
---------
""")
        for container in selected_containers:
            f.write(f"  • {container}\n")
        
        f.write("""

Import Instructions:
-------------------
1. Install ORCHIX on target server
2. Copy this package to ORCHIX/migrations/
3. Run: ORCHIX → Migration → Import Migration Package
4. Select this package
5. Done!

Notes:
------
- Backups are in """ + ("ZIP format (Windows)" if target_is_windows else "TAR.GZ format (Linux)") + """
- Ensure target server has Docker installed
- Ports must be available on target server

""")
    
    # Create tarball
    show_info("Creating archive...")
    tarball_path = MIGRATION_DIR / f"{package_name}.tar.gz"
    
    with tarfile.open(tarball_path, 'w:gz') as tar:
        tar.add(package_dir, arcname=package_name)
    
    # Cleanup temp directory
    shutil.rmtree(package_dir)
    
    # Show success
    print()
    show_success("Migration package created!")
    print()
    show_info(f"Package: {tarball_path}")
    show_info(f"Size: {_get_file_size(tarball_path)}")
    show_info(f"Target: {'Windows' if target_is_windows else 'Linux'}")
    print()
    show_info("Transfer to new server:")
    print(f"   scp {tarball_path} user@new-server:/path/to/ORCHIX/migrations/")
    print()
    show_info("Then on new server:")
    print("   ORCHIX → Migration → Import Migration Package")
    print()
    
    input("Press Enter...")


def _create_container_backup(container_name, output_dir, force_windows=None):
    '''
    Create backup for a container using hooks
    
    Args:
        container_name: Container to backup
        output_dir: Directory to save backup
        force_windows: Force Windows format (True) or Linux format (False)
                      If None, use current system
    
    Returns:
        Backup filename or None
    '''
    
    # Load manifests and hook loader
    from apps.manifest_loader import load_all_manifests
    from apps.hook_loader import get_hook_loader
    
    manifests = load_all_manifests()
    hook_loader = get_hook_loader()
    
    # Try to match container to manifest
    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    manifest = manifests.get(base_name)
    
    # If no manifest, try to detect from image
    if not manifest:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            image = result.stdout.strip().lower()
            
            # Try to match image to manifest
            for app_name, app_manifest in manifests.items():
                if app_name in image:
                    manifest = app_manifest
                    break
    
    # Create backup using hooks with platform override
    success = False
    if manifest and hook_loader.has_hook(manifest, 'backup'):
        # Temporarily override platform detection if needed
        if force_windows is not None:
            import utils.system
            original_is_windows = utils.system.is_windows
            utils.system.is_windows = lambda: force_windows

        try:
            success = hook_loader.execute_hook(manifest, 'backup', container_name)
        finally:
            # Restore original function
            if force_windows is not None:
                utils.system.is_windows = original_is_windows
    else:
        # Generic volume backup for template apps (no hooks)
        success = _generic_volume_backup(container_name, output_dir)
        if success:
            return f"{container_name}_volumes.tar.gz"

    if not success:
        return None

    # Find the created backup (most recent)
    # Determine pattern based on app type and target platform
    app_name = manifest.get('name', 'unknown') if manifest else 'unknown'

    # Determine target platform for backup format
    target_is_windows = force_windows if force_windows is not None else is_windows()

    if app_name == 'postgres':
        pattern = f"{container_name}_*.sql"
    elif target_is_windows:
        pattern = f"{container_name}_*.zip"
    else:
        pattern = f"{container_name}_*.tar.gz"

    backups = list(BACKUP_DIR.glob(pattern))
    if not backups:
        return None

    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)

    # Move to migration package
    dest = output_dir / latest_backup.name
    shutil.move(str(latest_backup), str(dest))

    # Move metadata too
    meta_src = _get_meta_file(latest_backup)
    if meta_src.exists():
        meta_dst = output_dir / meta_src.name
        shutil.move(str(meta_src), str(meta_dst))

    return latest_backup.name


def _generic_volume_backup(container_name, output_dir):
    """Generic backup: export all Docker volumes of a container."""
    from utils.docker_utils import safe_docker_run

    # Get volumes mounted on the container
    result = safe_docker_run(
        ['docker', 'inspect', container_name, '--format', '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{.Destination}}||{{end}}{{end}}'],
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    if not result or result.returncode != 0:
        return False

    volumes = []
    for part in result.stdout.strip().split('||'):
        part = part.strip()
        if not part:
            continue
        pieces = part.split(' ', 1)
        if len(pieces) == 2:
            volumes.append({'name': pieces[0], 'mount': pieces[1]})

    if not volumes:
        return False

    backup_file = output_dir / f"{container_name}_volumes.tar.gz"

    # Create tar.gz of all volume data using a temporary alpine container
    vol_args = []
    tar_paths = []
    for v in volumes:
        safe_name = v['name'].replace('/', '_')
        vol_args.extend(['-v', f"{v['name']}:/backup_src/{safe_name}:ro"])
        tar_paths.append(f'/backup_src/{safe_name}')

    cmd = ['docker', 'run', '--rm'] + vol_args + [
        '-v', f'{output_dir.resolve()}:/backup_dst',
        'alpine', 'tar', 'czf', f'/backup_dst/{container_name}_volumes.tar.gz'
    ] + tar_paths

    result = safe_docker_run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return result is not None and result.returncode == 0


def _get_hostname():
    '''Get system hostname'''
    try:
        import socket
        return socket.gethostname()
    except:
        return 'unknown'


def _get_file_size(filepath):
    '''Get human-readable file size'''
    size = Path(filepath).stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def _get_meta_file(backup_file):
    '''Get correct meta file path for backup (handles .tar.gz)'''
    
    # Handle .tar.gz files (double extension)
    if backup_file.suffix == '.gz' and backup_file.stem.endswith('.tar'):
        # Remove both .tar and .gz
        base_name = backup_file.stem[:-4]  # Remove .tar from stem
        return backup_file.parent / f"{base_name}.meta"
    else:
        # Single extension (.sql, .zip, .rdb)
        return backup_file.with_suffix('.meta')


def _wait_for_container_ready(container_name, timeout=30):
    '''Wait for container to be ready (using hooks)'''
    import time
    
    # Detect container type and get manifest
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        time.sleep(3)
        return
    
    image = result.stdout.strip().lower()
    
    # Try to match to manifest
    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()
    
    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    manifest = manifests.get(base_name)
    
    # If no manifest found, try to detect from image
    if not manifest:
        for app_name, app_manifest in manifests.items():
            if app_name in image:
                manifest = app_manifest
                break
    
    # Use hook if available
    if manifest:
        from apps.hook_loader import get_hook_loader
        hook_loader = get_hook_loader()
        
        if hook_loader.has_hook(manifest, 'ready_check'):
            hook_loader.execute_hook(manifest, 'ready_check', container_name, timeout)
            return
    
    # Fallback: generic wait (silent to avoid interrupting progress bar)
    time.sleep(5)


def import_migration_package():
    '''Import migration package'''
    
    show_panel("Import Migration Package", "Restore from migration package")
    
    # List available packages
    packages = list(MIGRATION_DIR.glob("orchix_migration_*.tar.gz"))
    
    if not packages:
        show_warning("No migration packages found!")
        print()
        show_info("Place migration packages in: migrations/")
        input("\nPress Enter...")
        return
    
    # Build choices
    choices = []
    for package in sorted(packages, reverse=True):
        size = _get_file_size(package)
        choices.append(f"{package.name} ({size})")
    
    choices.append("⬅️  Cancel")
    
    choice = select_from_list("Select migration package", choices)
    
    if "Cancel" in choice:
        return
    
    # Extract package name
    package_name = choice.split(' (')[0]
    package_path = MIGRATION_DIR / package_name
    
    # Extract package
    show_info("Extracting package...")
    extract_dir = MIGRATION_DIR / package_name.replace('.tar.gz', '')
    
    try:
        with tarfile.open(package_path, 'r:gz') as tar:
            tar.extractall(MIGRATION_DIR)
    except Exception as e:
        show_error(f"Failed to extract: {e}")
        input("\nPress Enter...")
        return
    
    # Read manifest with UTF-8
    manifest_file = extract_dir / 'migration_manifest.json'
    
    if not manifest_file.exists():
        show_error("Invalid migration package (no manifest)")
        input("\nPress Enter...")
        return
    
    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest_data = json.load(f)
    
    # Show package info
    print()
    show_info("Migration Package Info:")
    print(f"  Version: {manifest_data.get('version', 'unknown')}")
    print(f"  Created: {manifest_data.get('timestamp', 'unknown')}")
    print(f"  Source: {manifest_data.get('source_hostname', 'unknown')}")
    print(f"  Target Platform: {manifest_data.get('target_platform', 'unknown').upper()}")
    print(f"  Containers: {len(manifest_data.get('containers', []))}")
    print()
    show_info("Containers to import:")
    for container in manifest_data.get('containers', []):
        print(f"  • {container.get('name')}")
    print()
    
    # Confirm
    confirm = select_from_list(
        "Import all containers?",
        ["✅ Yes, import all", "⬅️  Cancel"]
    )
    
    if "Cancel" in confirm:
        # Cleanup
        shutil.rmtree(extract_dir)
        return
    
    # Load manifests for hooks
    from apps.manifest_loader import load_all_manifests
    from apps.hook_loader import get_hook_loader
    
    manifests = load_all_manifests()
    hook_loader = get_hook_loader()
    
    # Import each container with progress bar
    print()

    containers_list = manifest_data.get('containers', [])
    total_containers = len(containers_list)

    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        main_task = progress.add_task("Starting import...", total=total_containers * 100)

        for idx, container_data in enumerate(containers_list):
            container_name = container_data.get('name')
            progress.update(main_task, completed=idx * 100 + 10, description=f"Checking {container_name}...")

            # Check if container already exists
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            if container_name in result.stdout:
                progress.update(main_task, completed=(idx + 1) * 100, description=f"{container_name} already exists - skipped")
                continue

            # Copy compose file
            progress.update(main_task, completed=idx * 100 + 20, description=f"Installing {container_name}...")
            compose_file = container_data.get('compose_file')
            if compose_file:
                compose_src = extract_dir / compose_file
                compose_dst = Path(compose_file)

                if compose_src.exists():
                    shutil.copy2(compose_src, compose_dst)

            # Deploy container
            progress.update(main_task, completed=idx * 100 + 40, description=f"Starting {container_name}...")
            result = subprocess.run(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                progress.update(main_task, completed=(idx + 1) * 100, description=f"{container_name} failed to start")
                continue

            # Wait for container to be ready
            progress.update(main_task, completed=idx * 100 + 60, description=f"Initializing {container_name}...")
            _wait_for_container_ready(container_name)

            # Restore backup using hooks
            progress.update(main_task, completed=idx * 100 + 80, description=f"Restoring {container_name}...")
            backup_file = container_data.get('backup_file')
            if backup_file:
                backup_src = extract_dir / backup_file
                backup_dst = BACKUP_DIR / backup_file

                if backup_src.exists():
                    # Move backup to backups directory
                    shutil.copy2(backup_src, backup_dst)

                    # Move metadata too
                    meta_src_path = _get_meta_file(Path(extract_dir / backup_file))
                    if meta_src_path.exists():
                        meta_dst = _get_meta_file(backup_dst)
                        shutil.copy2(meta_src_path, meta_dst)

                    # Get manifest for restore
                    base_name = container_name.split('_')[0] if '_' in container_name else container_name
                    app_manifest = manifests.get(base_name)

                    # If no manifest, try to detect from container
                    if not app_manifest:
                        result = subprocess.run(
                            ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore'
                        )

                        if result.returncode == 0:
                            image = result.stdout.strip().lower()

                            for app_name, manifest in manifests.items():
                                if app_name in image:
                                    app_manifest = manifest
                                    break

                    # Restore using hooks (skip silently if no hook exists)
                    if app_manifest and hook_loader.has_hook(app_manifest, 'restore'):
                        hook_loader.execute_hook(app_manifest, 'restore', backup_dst, container_name)

            progress.update(main_task, completed=(idx + 1) * 100, description=f"✅ {idx + 1}/{total_containers} imported")
    
    # Cleanup
    shutil.rmtree(extract_dir)
    
    print()
    show_success("Migration complete!")
    print()
    show_info("All containers have been imported and restored.")
    print()
    
    input("Press Enter...")


def list_migration_packages():
    '''List available migration packages'''
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    show_info("Loading migration packages...")
    print()
    
    packages = list(MIGRATION_DIR.glob("orchix_migration_*.tar.gz"))
    
    if not packages:
        show_warning("No migration packages found!")
    else:
        table = Table(title="Available Migration Packages", show_header=True, header_style="bold cyan")
        table.add_column("Package", style="cyan", width=40)
        table.add_column("Size", style="white", width=15)
        table.add_column("Created", style="dim", width=20)
        
        for package in sorted(packages, reverse=True):
            size = _get_file_size(package)
            created = datetime.fromtimestamp(package.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            table.add_row(package.name, size, created)
        
        console.print()
        console.print(table)
        console.print()
    
    input("\nPress Enter...")


def show_migration_guide():
    '''Show migration guide'''
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    guide = """[bold cyan]Server Migration Guide[/bold cyan]

[bold]EXPORT (Source Server):[/bold]
1. Migration → Export Migration Package
2. Select containers to migrate
3. Choose target platform (Linux/Windows)
4. Package created in migrations/ directory
5. Transfer: scp package user@new-server:/path/

[bold]IMPORT (Target Server):[/bold]
1. Install ORCHIX on new server
2. Copy package to migrations/ directory
3. Migration → Import Migration Package
4. Select package and confirm
5. ✅ Done! Containers migrated

[bold yellow]⚠️  Important Notes:[/bold yellow]
- Select correct target platform for backups
- Containers must not exist on target server
- Same Docker network will be created
- Ports must be available
- ORCHIX version should match

[bold green]💡 Tips:[/bold green]
- Windows → Linux: Select "Linux" format
- Linux → Windows: Select "Windows" format
- Test import on non-production first
- Keep original backups safe
- Document port mappings
- Verify after migration
"""
    
    panel = Panel(
        guide,
        title="[bold cyan]📚 Migration Guide[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)
    print()
    
    input("Press Enter...")