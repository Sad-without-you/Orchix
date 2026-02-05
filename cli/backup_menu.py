import subprocess
import os
from pathlib import Path
from datetime import datetime
from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning
from rich.console import Console
from rich.table import Table

# Backup directory
BACKUP_DIR = Path('backups')
BACKUP_DIR.mkdir(exist_ok=True)


def show_backup_menu():
    '''Backup and restore menu'''
    
    while True:
        show_panel("Backup & Restore", "Backup and restore container data")
        
        choices = [
            "💾 Create Backup",
            "♻️  Restore from Backup",
            "📋 List Backups",
            "🗑️  Delete Backup",
            "⬅️  Back to Main Menu"
        ]
        
        choice = select_from_list("Select action", choices)
        
        if "Back to Main Menu" in choice:
            break
        
        if "Create" in choice:
            create_backup_menu()
        elif "Restore" in choice:
            restore_backup_menu()
        elif "List" in choice:
            list_backups()
        elif "Delete" in choice:
            delete_backup_menu()


def create_backup_menu():
    '''Create backup menu - Dynamic with hooks'''
    
    show_panel("Create Backup", "Select container to backup")
    
    # Get all running containers
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
    except FileNotFoundError:
        show_error("Docker is not installed! Please install Docker first (Setup > Install Docker)")
        input("Press Enter...")
        return

    if result.returncode != 0:
        show_error("Failed to get containers. Is Docker running?")
        input("Press Enter...")
        return
    
    containers = [c for c in result.stdout.split('\n') if c]
    
    if not containers:
        show_info("No containers running!")
        input("Press Enter...")
        return
    
    # Load manifests
    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()
    
    # Build choices with icons from manifests
    choices = []
    container_manifest_map = {}
    
    for container in containers:
        # Try to match container to manifest
        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name) or manifests.get(container)
        
        if manifest:
            icon = manifest.get('icon', '📦')
            choices.append(f"{icon} {container}")
            container_manifest_map[container] = manifest
        else:
            choices.append(f"📦 {container}")
            container_manifest_map[container] = None
    
    choices.append("⬅️  Cancel")
    
    # User selects container
    choice = select_from_list("Select container to backup", choices)
    
    if "Cancel" in choice:
        return
    
    # Extract container name
    container_name = None
    for container in containers:
        if container in choice:
            container_name = container
            break
    
    if not container_name:
        show_error("Invalid selection")
        input("Press Enter...")
        return
    
    # Get manifest for container
    manifest = container_manifest_map.get(container_name)
    
    # Create backup
    show_info(f"Creating backup for {container_name}...")
    print()
    
    if manifest:
        # Use hook-based backup
        from apps.hook_loader import get_hook_loader
        hook_loader = get_hook_loader()
        
        if hook_loader.has_hook(manifest, 'backup'):
            success = hook_loader.execute_hook(manifest, 'backup', container_name)
        else:
            show_warning(f"No backup hook available for {manifest['name']}")
            success = False
    else:
        # Fallback: generic backup (for unknown containers)
        show_warning("No manifest found - backup not supported")
        success = False
    
    if success:
        show_success("Backup created successfully!")
    else:
        show_error("Backup failed!")
    
    print()
    input("Press Enter...")


def restore_backup_menu():
    '''Restore from backup menu - App selection first, dynamic with hooks'''
    
    show_panel("Restore from Backup", "Select app to restore")
    
    # Get all backups
    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))
    
    if not backups:
        show_warning("No backups found!")
        input("Press Enter...")
        return
    
    # Group backups by app type
    apps_with_backups = {}
    
    for backup in backups:
        meta_file = backup.with_suffix('.meta')
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                container = lines[0].split(':')[1].strip()
                app_type = lines[1].split(':')[1].strip()
                
                if container not in apps_with_backups:
                    apps_with_backups[container] = {
                        'type': app_type,
                        'backups': []
                    }
                
                apps_with_backups[container]['backups'].append(backup)
    
    if not apps_with_backups:
        show_warning("No valid backups found!")
        input("Press Enter...")
        return
    
    # Load manifests for icon display
    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()
    
    # Step 1: Select App
    app_choices = []
    for container, info in sorted(apps_with_backups.items()):
        app_type = info['type']
        count = len(info['backups'])
        
        # Try to get icon from manifest
        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name) or manifests.get(app_type)
        
        if manifest:
            icon = manifest.get('icon', '📦')
        else:
            # Fallback icons
            if app_type == 'postgres':
                icon = "🐘"
            elif app_type == 'n8n':
                icon = "⚡"
            elif app_type == 'redis':
                icon = "🔴"
            else:
                icon = "📦"
        
        app_choices.append(f"{icon} {container} ({count} backups)")
    
    app_choices.append("⬅️  Cancel")
    
    selected_app = select_from_list("Select app to restore", app_choices)
    
    if "Cancel" in selected_app:
        return
    
    # Extract container name
    container_name = selected_app.split(' ')[1]
    
    # Step 2: Select Backup for this app
    app_backups = apps_with_backups[container_name]['backups']
    
    backup_choices = []
    for backup in sorted(app_backups, reverse=True):
        # Read metadata for timestamp
        meta_file = backup.with_suffix('.meta')
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                timestamp = lines[2].split(':')[1].strip()[:19] if len(lines) > 2 else 'Unknown'
        else:
            timestamp = 'Unknown'
        
        backup_choices.append(f"{timestamp} - {backup.name}")
    
    backup_choices.append("⬅️  Cancel")
    
    selected_backup_choice = select_from_list(
        f"Select backup for {container_name}",
        backup_choices
    )
    
    if "Cancel" in selected_backup_choice:
        return
    
    # Extract backup filename
    backup_name = selected_backup_choice.split(' - ')[1]
    selected_backup = BACKUP_DIR / backup_name
    
    # Read metadata
    meta_file = selected_backup.with_suffix('.meta')
    if not meta_file.exists():
        show_error("Metadata file not found!")
        input("Press Enter...")
        return
    
    with open(meta_file, 'r') as f:
        lines = f.readlines()
        container_name = lines[0].split(':')[1].strip()
        app_type = lines[1].split(':')[1].strip()
    
    # Confirm restore
    show_warning(f"This will OVERWRITE current data in {container_name}!")
    print()
    
    confirm = select_from_list(
        "Are you sure?",
        ["✅ Yes, restore backup", "⬅️  Cancel"]
    )
    
    if "Cancel" in confirm:
        show_info("Restore cancelled")
        input("Press Enter...")
        return
    
    # Get manifest for restore
    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    manifest = manifests.get(base_name) or manifests.get(app_type)
    
    # Execute restore
    show_info(f"Restoring {app_type} backup...")
    
    if manifest:
        # Use hook-based restore
        from apps.hook_loader import get_hook_loader
        hook_loader = get_hook_loader()
        
        if hook_loader.has_hook(manifest, 'restore'):
            success = hook_loader.execute_hook(manifest, 'restore', selected_backup, container_name)
        else:
            show_warning(f"No restore hook available for {manifest['name']}")
            success = False
    else:
        # Fallback: restore not supported
        show_warning("No manifest found - restore not supported")
        success = False
    
    if success:
        show_success("Restore completed!")
        print()

        # Check if image version differs from backup
        _check_image_version(meta_file, container_name)
    else:
        show_error("Restore failed!")

    print()
    input("Press Enter...")


def create_metadata(container_name, backup_file, app_type):
    '''Create metadata file for backup'''

    meta_file = backup_file.with_suffix('.meta')

    # Get Docker image version from container
    image_version = "unknown"
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            image_version = result.stdout.strip()
    except Exception:
        pass  # If we can't get version, use "unknown"

    with open(meta_file, 'w') as f:
        f.write(f"Container: {container_name}\n")
        f.write(f"Type: {app_type}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"File: {backup_file.name}\n")
        f.write(f"Image: {image_version}\n")


def list_backups():
    '''List all backups'''
    console = Console()
    
    show_info("Loading backups...")
    print()
    
    # Get all backups
    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))
    
    if not backups:
        show_warning("No backups found!")
    else:
        # Load manifests for icon display
        from apps.manifest_loader import load_all_manifests
        manifests = load_all_manifests()
        
        table = Table(title="📋 Available Backups", show_header=True, header_style="bold cyan")
        table.add_column("Container", style="cyan", width=20)
        table.add_column("Type", style="white", width=15)
        table.add_column("Format", style="dim", width=10)
        table.add_column("Date", style="white", width=20)
        table.add_column("File", style="dim", width=30)
        
        for backup in sorted(backups, reverse=True):
            # Read metadata
            meta_file = backup.with_suffix('.meta')
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    lines = f.readlines()
                    container = lines[0].split(':')[1].strip()
                    app_type = lines[1].split(':')[1].strip()
                    timestamp = lines[2].split(':')[1].strip()[:19]
                    
                    # Get icon from manifest
                    base_name = container.split('_')[0] if '_' in container else container
                    manifest = manifests.get(base_name) or manifests.get(app_type)
                    
                    if manifest:
                        icon = manifest.get('icon', '📦')
                        type_display = f"{icon} {manifest['display_name']}"
                    else:
                        # Fallback icons
                        if app_type == 'postgres':
                            type_display = "🐘 PostgreSQL"
                        elif app_type == 'n8n':
                            type_display = "⚡ n8n"
                        elif app_type == 'redis':
                            type_display = "🔴 Redis"
                        else:
                            type_display = f"📦 {app_type}"
                    
                    # Format indicator
                    if backup.suffix == '.zip':
                        format_display = "📦 ZIP"
                    elif backup.suffix == '.gz':
                        format_display = "📦 TAR.GZ"
                    elif backup.suffix == '.sql':
                        format_display = "💾 SQL"
                    elif backup.suffix == '.rdb':
                        format_display = "🔴 RDB"
                    else:
                        format_display = backup.suffix
                    
                    table.add_row(container, type_display, format_display, timestamp, backup.name)
            else:
                table.add_row("Unknown", "Unknown", "Unknown", "Unknown", backup.name)
        
        console.print()
        console.print(table)
        console.print()
    
    input("\nPress Enter...")


def delete_backup_menu():
    '''Delete backup menu - App selection first'''
    
    show_panel("Delete Backup", "Select app")
    
    # Get all backups
    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))
    
    if not backups:
        show_warning("No backups found!")
        input("Press Enter...")
        return
    
    # Group backups by app
    apps_with_backups = {}
    
    for backup in backups:
        meta_file = backup.with_suffix('.meta')
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                container = lines[0].split(':')[1].strip()
                app_type = lines[1].split(':')[1].strip()
                
                if container not in apps_with_backups:
                    apps_with_backups[container] = {
                        'type': app_type,
                        'backups': []
                    }
                
                apps_with_backups[container]['backups'].append(backup)
    
    if not apps_with_backups:
        show_warning("No valid backups found!")
        input("Press Enter...")
        return
    
    # Load manifests for icon display
    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()
    
    # Step 1: Select App
    app_choices = []
    for container, info in sorted(apps_with_backups.items()):
        app_type = info['type']
        count = len(info['backups'])
        
        # Get icon from manifest
        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name) or manifests.get(app_type)
        
        if manifest:
            icon = manifest.get('icon', '📦')
        else:
            # Fallback icons
            if app_type == 'postgres':
                icon = "🐘"
            elif app_type == 'n8n':
                icon = "⚡"
            elif app_type == 'redis':
                icon = "🔴"
            else:
                icon = "📦"
        
        app_choices.append(f"{icon} {container} ({count} backups)")
    
    app_choices.append("⬅️  Cancel")
    
    selected_app = select_from_list("Select app", app_choices)
    
    if "Cancel" in selected_app:
        return
    
    # Extract container name
    container_name = selected_app.split(' ')[1]
    
    # Step 2: Select Backup to delete
    app_backups = apps_with_backups[container_name]['backups']
    
    backup_choices = []
    for backup in sorted(app_backups, reverse=True):
        # Read metadata for timestamp
        meta_file = backup.with_suffix('.meta')
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                timestamp = lines[2].split(':')[1].strip()[:19] if len(lines) > 2 else 'Unknown'
        else:
            timestamp = 'Unknown'
        
        backup_choices.append(f"{timestamp} - {backup.name}")
    
    backup_choices.append("⬅️  Cancel")
    
    selected_backup_choice = select_from_list(
        f"Select backup to delete",
        backup_choices
    )
    
    if "Cancel" in selected_backup_choice:
        return
    
    # Extract backup filename
    backup_name = selected_backup_choice.split(' - ')[1]
    selected_backup = BACKUP_DIR / backup_name
    
    # Confirm deletion
    show_warning(f"This will permanently delete: {backup_name}")
    print()
    
    confirm = select_from_list(
        "Are you sure?",
        ["❌ Yes, delete backup", "⬅️  Cancel"]
    )
    
    if "Cancel" in confirm:
        show_info("Deletion cancelled")
        input("Press Enter...")
        return
    
    # Delete backup and metadata
    try:
        selected_backup.unlink()
        
        meta_file = selected_backup.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
        
        show_success("Backup deleted!")
    except Exception as e:
        show_error(f"Failed to delete backup: {e}")

    print()
    input("Press Enter...")


def _check_image_version(meta_file, container_name):
    '''Check if container image version matches backup and offer to recreate'''

    # Read image version from metadata
    backup_image = None
    try:
        with open(meta_file, 'r') as f:
            for line in f:
                if line.startswith('Image:'):
                    backup_image = line.split(':', 1)[1].strip()
                    break
    except:
        return  # Can't read metadata, skip check

    if not backup_image or backup_image == "unknown":
        return  # No image info in backup

    # Get current container image
    current_image = None
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            current_image = result.stdout.strip()
    except:
        return  # Can't inspect container

    if not current_image or current_image == backup_image:
        return  # Same version, no action needed

    # Versions differ - ask user if they want to recreate container
    show_warning(f"Image version mismatch detected!")
    print(f"   Current:  {current_image}")
    print(f"   Backup:   {backup_image}")
    print()

    choice = select_from_list(
        "Do you want to recreate the container with the backup version?",
        [
            f"✅ Yes, use {backup_image}",
            f"❌ No, keep {current_image}"
        ]
    )

    if "No" in choice:
        show_info("Container will keep current image version")
        return

    # Recreate container with backup image version
    show_info(f"Recreating container with {backup_image}...")
    print()

    # Find compose file
    compose_file = f"docker-compose-{container_name}.yml"
    if not Path(compose_file).exists():
        show_error(f"docker-compose file not found: {compose_file}")
        show_info("Please manually update the image version in your compose file")
        return

    # Update image version in compose file
    try:
        with open(compose_file, 'r') as f:
            compose_content = f.read()

        # Replace image line (assuming format: "image: xxx:tag")
        import re
        updated_content = re.sub(
            r'(\s+image:\s+)([^\n]+)',
            f'\\1{backup_image}',
            compose_content
        )

        with open(compose_file, 'w') as f:
            f.write(updated_content)

        show_success("Updated compose file")

        # Recreate container
        show_info("Recreating container...")
        result = subprocess.run(
            ['docker', 'compose', '-f', compose_file, 'up', '-d', '--force-recreate'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            show_success(f"Container recreated with {backup_image}")
        else:
            show_error(f"Failed to recreate container: {result.stderr}")

    except Exception as e:
        show_error(f"Failed to update container: {e}")