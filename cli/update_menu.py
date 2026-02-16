from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_step, show_step_final, show_step_detail
from apps.manifest_loader import load_all_manifests
from license.audit_logger import get_audit_logger, AuditEventType
from license import get_license_manager
import subprocess
import re
import os
from utils.docker_utils import safe_docker_run, get_docker_compose_command
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

console = Console()


def get_installed_containers():
    '''Get list of running containers'''
    result = safe_docker_run(
        ['docker', 'ps', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return []
    if result.returncode == 0:
        return [c for c in result.stdout.split('\n') if c]
    return []


def show_update_menu():
    '''Generic update menu for all apps'''
    
    while True:
        show_panel("Update Applications", "Update installed containers")
        
        # Get installed containers
        containers = get_installed_containers()
        
        if not containers:
            show_info("No containers running!")
            input("Press Enter...")
            break
        
        # Load manifests
        manifests = load_all_manifests()
        
        # Build choices
        choices = []
        for container in containers:
            manifest = _resolve_manifest(container, manifests)

            if manifest:
                icon = manifest.get('icon', '📦')
                display = f"{icon} {container}"
            else:
                display = f"📦 {container}"

            choices.append(display)
        
        choices.append("⬅️  Back to Main Menu")
        
        # User selects
        choice = select_from_list("Select container to update", choices)
        
        if "Back" in choice:
            break
        
        # Extract container name from choice
        container_name = None
        for container in containers:
            if container in choice:
                container_name = container
                break
        
        if container_name:
            manifest = _resolve_manifest(container_name, manifests)
            update_app(container_name, manifest)


def update_app(container_name, manifest):
    '''Update a specific app'''
    
    if not manifest:
        show_error(f"No manifest found for {container_name}")
        input("Press Enter...")
        return
    
    show_panel(f"Updating {container_name}", "Select update action")
    
    # Get updater class
    UpdaterClass = manifest.get('updater_class')
    
    if not UpdaterClass:
        show_error(f"No updater available")
        input("Press Enter...")
        return
    
    # Create updater
    updater = UpdaterClass(manifest)
    
    # Get available actions
    actions = updater.get_available_actions()
    
    if not actions:
        show_info("No update actions available")
        input("Press Enter...")
        return
    
    # Build action choices
    action_choices = []
    for action in actions:
        if action == 'version_update':
            action_choices.append("🔄 Update to Latest (Stable)")
        elif action == 'config_update':
            action_choices.append("⚙️  Configuration Update")
        elif action == 'beta_update':
            action_choices.append("🆕 Update to Beta")
        elif action == 'next_update':
            action_choices.append("🛠️  Update to next")

    action_choices.append("⬅️  Cancel")
    
    # User selects action
    choice = select_from_list("Select update action", action_choices)
    
    if "Cancel" in choice:
        return
    
    # Execute selected action with progress bar
    success = False

    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Starting update...", total=100)

        try:
            # Step 1: Pull new image and update (0% -> 75%)
            progress.update(task, completed=25, description="Pulling new image...")

            if "Latest" in choice:
                success = updater.version_update()
            elif "Configuration" in choice:
                success = updater.config_update()
            elif "Beta" in choice:
                success = updater.beta_update()
            elif "next" in choice:
                success = updater.next_update()

            if not success:
                progress.update(task, completed=100, description="Update failed!")
            else:
                # Step 2: Re-tag and restart (75% -> 100%)
                progress.update(task, completed=75, description="Applying update...")
                _retag_after_update(container_name)
                progress.update(task, completed=100, description="Update complete!")

        except Exception as e:
            progress.update(task, completed=100, description=f"Update error: {e}")
            success = False

    if success:
        show_step_final("Update complete!", True)
    else:
        show_step_final("Update failed!", False)
    
    # Log audit event for PRO users
    license_manager = get_license_manager()
    audit_logger = get_audit_logger(enabled=license_manager.is_pro())
    
    update_type = "unknown"
    if "Latest" in choice:
        update_type = "version_update"
    elif "Configuration" in choice:
        update_type = "config_update"
    elif "Beta" in choice:
        update_type = "beta_update"
    elif "next" in choice:
        update_type = "next_update"
    
    audit_logger.log_event(
        AuditEventType.UPDATE,
        container_name,
        {
            'update_type': update_type,
            'status': 'success' if success else 'failed'
        }
    )
    
    input("\nPress Enter...")


def _resolve_manifest(container_name, manifests):
    '''Resolve a container name to its app manifest.
    Handles instances like n8n2, n8n-dev, n8n_custom -> manifest "n8n".'''
    # 1. Exact match
    if container_name in manifests:
        return manifests[container_name]

    # 2. Split by _ (e.g. postgres_prod -> postgres)
    if '_' in container_name:
        base = container_name.split('_')[0]
        if base in manifests:
            return manifests[base]

    # 3. Longest prefix match (e.g. n8n2 -> n8n, grafana3 -> grafana)
    # Only match if suffix is a digit or separator, not a letter
    # (prevents "rediscover" matching "redis")
    best_match = None
    best_len = 0
    for app_name in manifests:
        if container_name.startswith(app_name) and len(app_name) > best_len:
            rest = container_name[len(app_name):]
            if not rest or rest[0].isdigit() or rest[0] in ('-', '_'):
                best_match = app_name
                best_len = len(app_name)

    if best_match:
        return manifests[best_match]

    return None


def _retag_after_update(container_name):
    '''Re-tag the source image after an update for orchix-tagged containers'''
    compose_file = f"docker-compose-{container_name}.yml"
    if not os.path.exists(compose_file):
        return

    with open(compose_file, 'r') as f:
        content = f.read()

    # Check if this is an orchix-tagged container
    instance_image = f"{container_name}:orchix"
    if f'image: {instance_image}' not in content:
        return  # Old-style container, no re-tagging needed

    # Read source image from comment
    match = re.search(r'# orchix_source_image:\s*(.+)', content)
    if not match:
        return

    source_image = match.group(1).strip()

    # Re-tag the (newly pulled) source image as the instance tag
    result = safe_docker_run(
        ['docker', 'tag', source_image, instance_image],
        capture_output=True, text=True
    )
    if not result or result.returncode != 0:
        return

    # Recreate container with the updated image
    show_step_detail("Applying updated image...")
    docker_compose_cmd = get_docker_compose_command()
    safe_docker_run(
        docker_compose_cmd + ['-f', compose_file, 'up', '-d'],
        capture_output=True, text=True
    )