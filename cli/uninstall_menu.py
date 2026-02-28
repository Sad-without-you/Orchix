from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning, show_step, show_step_final, show_step_detail, show_result_panel
import subprocess
import os
import shutil
from pathlib import Path
from license.audit_logger import get_audit_logger, AuditEventType
from license import get_license_manager
from utils.docker_utils import get_docker_compose_command, safe_docker_run
from config import ORCHIX_CONFIG_DIR
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

console = Console()


def get_all_containers():
    '''Get ALL containers (including stopped)'''
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return []
    if result.returncode == 0:
        return [c for c in result.stdout.split('\n') if c]
    return []


def show_uninstall_menu():
    '''Uninstall menu - remove containers and data'''
    
    while True:
        show_panel("Uninstall Applications", "Remove containers and volumes")
        
        # Get all containers
        containers = get_all_containers()
        
        if not containers:
            show_info("No containers found!")
            input("Press Enter...")
            break
        
        # Build choices
        choices = []
        for container in containers:
            # Check if running
            result = safe_docker_run(
                ['docker', 'ps', '--filter', f'name=^{container}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            if result is None:
                show_error("Docker is not available!")
                input("Press Enter...")
                return
            is_running = container in result.stdout
            
            if is_running:
                choices.append(f"🟢 {container} (running)")
            else:
                choices.append(f"🔴 {container} (stopped)")
        
        choices.append("⬅️  Back to Main Menu")
        
        # User selects
        choice = select_from_list("Select container to remove", choices)
        
        if "Back" in choice:
            break
        
        # Extract container name
        container_name = choice.split(' ')[1]  # "🟢 n8n (running)" -> "n8n"
        
        # Uninstall
        uninstall_container(container_name)


def uninstall_container(container_name):
    '''Uninstall a container with confirmation - removes EVERYTHING'''
    
    show_panel(f"Uninstall {container_name}", "Remove container and ALL associated data")
    
    # Get list of volumes - find all docker volumes starting with container_name
    result = safe_docker_run(
        ['docker', 'volume', 'ls', '--filter', f'name=^{container_name}_', '--format', '{{.Name}}'],
        capture_output=True,
        text=True
    )

    volumes_to_delete = []
    if result is None:
        show_error("Docker is not available!")
        input("Press Enter...")
        return
    if result.returncode == 0:
        volumes_to_delete = [v.strip() for v in result.stdout.split('\n') if v.strip()]
    
    # Fallback: read from docker-compose file
    if not volumes_to_delete:
        compose_file = f"docker-compose-{container_name}.yml"
        if os.path.exists(compose_file):
            try:
                with open(compose_file, 'r') as f:
                    content = f.read()
                
                import re
                # Find all volume definitions: word followed by colon at line start (after spaces)
                vol_matches = re.findall(r'^\s{2}(\w+):\s*$', content, re.MULTILINE)
                volumes_to_delete = vol_matches
            except:
                pass
    
    # Final fallback to standard naming
    if not volumes_to_delete:
        volumes_to_delete = [f"{container_name}_data"]
    
    # Collect ALL files that will be deleted
    files_to_delete = []

    # 1. Docker compose file
    compose_file = f"docker-compose-{container_name}.yml"
    if os.path.exists(compose_file):
        files_to_delete.append(compose_file)

    # 2. Dockerfile (for apps that build custom images)
    dockerfile = f"Dockerfile-{container_name}"
    if os.path.exists(dockerfile):
        files_to_delete.append(dockerfile)
    
    # 2. Config files in /config directory
    config_dir = Path("config")
    if config_dir.exists():
        for config_file in config_dir.glob(f"{container_name}*"):
            files_to_delete.append(str(config_file))
    
    # 3. Temp files in various locations
    temp_patterns = [
        Path("tmp") / f"{container_name}*",
        Path(".temp") / f"{container_name}*",
        ORCHIX_CONFIG_DIR / f".orchix_{container_name}*",
    ]
    
    for pattern in temp_patterns:
        if "*" in str(pattern):
            parent = pattern.parent
            if parent.exists():
                for temp_file in parent.glob(pattern.name):
                    files_to_delete.append(str(temp_file))
    
    # Show what will be deleted
    show_warning("  COMPLETE REMOVAL - This will delete:")
    show_info(f"   • Container: {container_name}")
    for vol in volumes_to_delete:
        show_info(f"   • Volume: {vol}")
    
    if files_to_delete:
        show_info("   • Files:")
        for file in files_to_delete:
            show_info(f"      - {file}")
    
    print()
    show_warning("This action CANNOT be undone!")
    print()
    
    # Confirm with double-check
    confirm = select_from_list(
        "Are you absolutely sure you want to remove everything?",
        ["❌ Yes, remove EVERYTHING", "⬅️  Cancel"]
    )
    
    if "Cancel" in confirm:
        show_info("Uninstall cancelled")
        input("Press Enter...")
        return
    
    # Initialize audit logger
    license_manager = get_license_manager()
    audit_logger = get_audit_logger(enabled=license_manager.is_pro())

    # Execute removal with detailed logging and progress bar
    removal_details = {
        'volumes_removed': [],
        'files_removed': [],
        'errors': []
    }

    compose_file = f"docker-compose-{container_name}.yml"

    # Progress bar for uninstall process
    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Starting removal...", total=100)

        # 0. Collect images BEFORE removal (inspect won't work after container is gone)
        images_to_remove = _get_container_images(container_name, compose_file)

        # 1. Stop and remove container directly (NOT docker compose down, which
        # shares a project name across all compose files in the same directory
        # and can stop/remove OTHER containers from the same project)
        progress.update(task, completed=10, description="Removing container...")

        # Stop the container
        result = safe_docker_run(
            ['docker', 'stop', container_name],
            capture_output=True, text=True
        )
        if result is None:
            removal_details['errors'].append("Docker not available")
        elif result and result.returncode != 0:
            removal_details['errors'].append("Container stop failed")

        # Remove the container
        result = safe_docker_run(
            ['docker', 'rm', '-f', container_name],
            capture_output=True, text=True
        )
        if result and result.returncode != 0 and "No such container" not in result.stderr:
            removal_details['errors'].append(f"Container removal: {result.stderr.strip()}")

        progress.update(task, completed=20, description="Container removed")

        # 1b. Remove volumes belonging to THIS instance only
        progress.update(task, completed=30, description="Removing volumes...")
        result = safe_docker_run(
            ['docker', 'volume', 'ls', '--format', '{{.Name}}'],
            capture_output=True, text=True
        )
        if result is not None and result.returncode == 0:
            all_volumes = result.stdout.strip().split('\n')
            for vol in all_volumes:
                if vol and _volume_belongs_to_instance(vol, container_name):
                    remove_result = safe_docker_run(
                        ['docker', 'volume', 'rm', '-f', vol],
                        capture_output=True, text=True
                    )
                    if remove_result is None:
                        continue
                    if remove_result.returncode == 0:
                        removal_details['volumes_removed'].append(vol)
                    else:
                        if "no such volume" not in remove_result.stderr.lower():
                            removal_details['errors'].append(f"Volume {vol}: {remove_result.stderr.strip()}")

        progress.update(task, completed=45, description="Volumes removed")

        # 2. Remove compose file
        progress.update(task, completed=50, description="Cleaning up files...")
        if os.path.exists(compose_file):
            try:
                os.remove(compose_file)
                removal_details['files_removed'].append(compose_file)
            except Exception as e:
                removal_details['errors'].append(f"Compose file removal: {str(e)}")

        # 3. Remove Dockerfile (if exists)
        dockerfile = f"Dockerfile-{container_name}"
        if os.path.exists(dockerfile):
            try:
                os.remove(dockerfile)
                removal_details['files_removed'].append(dockerfile)
            except Exception as e:
                removal_details['errors'].append(f"Dockerfile removal: {str(e)}")

        # 3. Remove config files
        config_dir = Path("config")
        if config_dir.exists():
            for config_file in config_dir.glob(f"{container_name}*"):
                try:
                    if config_file.is_file():
                        config_file.unlink()
                        removal_details['files_removed'].append(str(config_file))
                    elif config_file.is_dir():
                        shutil.rmtree(config_file)
                        removal_details['files_removed'].append(str(config_file))
                except Exception as e:
                    removal_details['errors'].append(f"Config removal {config_file.name}: {str(e)}")

        # 4. Remove temp files
        temp_patterns = [
            (Path("tmp"), f"{container_name}*"),
            (Path(".temp"), f"{container_name}*"),
            (ORCHIX_CONFIG_DIR, f".orchix_{container_name}*"),
        ]

        for temp_dir, pattern in temp_patterns:
            if temp_dir.exists():
                try:
                    for temp_file in temp_dir.glob(pattern):
                        if temp_file.is_file():
                            temp_file.unlink()
                            removal_details['files_removed'].append(str(temp_file))
                        elif temp_file.is_dir():
                            shutil.rmtree(temp_file)
                            removal_details['files_removed'].append(str(temp_file))
                except Exception as e:
                    removal_details['errors'].append(f"Temp cleanup {temp_dir}: {str(e)}")

        progress.update(task, completed=65, description="Files cleaned up")

        # 7. Docker cleanup - remove images only if no other container uses them
        progress.update(task, completed=70, description="Docker cleanup...")

        # Remove instance-specific image tag (e.g. n8n:orchix, n8n2:orchix)
        # These are unique per instance, so safe to remove without in-use checks
        instance_image = f"{container_name}:orchix"
        result = safe_docker_run(
            ['docker', 'rmi', instance_image],
            capture_output=True, text=True
        )
        if result and result.returncode == 0:
            removal_details['files_removed'].append(f"Image: {instance_image}")

        # Fallback for old-style containers (pre instance-tagging)
        # Only remove shared images if NO other container uses the same repository
        repos_in_use = set()
        result = safe_docker_run(
            ['docker', 'ps', '-a', '--format', '{{.Image}}'],
            capture_output=True, text=True
        )
        if result and result.returncode == 0:
            for img in result.stdout.strip().split('\n'):
                img = img.strip()
                if img:
                    repo = img.rsplit(':', 1)[0] if ':' in img else img
                    repos_in_use.add(repo)

        for image in images_to_remove:
            if image == instance_image:
                continue  # Already handled above
            img_repo = image.rsplit(':', 1)[0] if ':' in image else image
            if img_repo in repos_in_use:
                continue
            remove_result = safe_docker_run(
                ['docker', 'rmi', image],
                capture_output=True, text=True
            )
            if remove_result is None:
                continue
            if remove_result.returncode == 0:
                removal_details['files_removed'].append(f"Image: {image}")

        # Remove dangling volumes ONLY if they belong to THIS instance
        result = safe_docker_run(
            ['docker', 'volume', 'ls', '--filter', 'dangling=true', '--format', '{{.Name}}'],
            capture_output=True,
            text=True
        )

        if result is not None and result.returncode == 0:
            dangling_volumes = result.stdout.strip().split('\n')
            for vol in dangling_volumes:
                if vol and _volume_belongs_to_instance(vol, container_name):
                    remove_result = safe_docker_run(
                        ['docker', 'volume', 'rm', vol],
                        capture_output=True,
                        text=True
                    )

                    if remove_result is None:
                        continue
                    if remove_result.returncode == 0:
                        removal_details['volumes_removed'].append(vol)

        # Clean up unused networks only (NOT volumes - other instances may use them)
        progress.update(task, completed=90, description="System cleanup...")
        prune_result = safe_docker_run(
            ['docker', 'network', 'prune', '-f'],
            capture_output=True,
            text=True
        )

        progress.update(task, completed=100, description="Uninstall complete!")

        # 8. Log audit event
        audit_logger.log_event(
            AuditEventType.UNINSTALL,
            container_name,
            removal_details
        )
    
    # Summary
    show_step_final(f"{container_name} completely uninstalled!", True)

    summary = f"Removed {len(removal_details['volumes_removed'])} volume(s), {len(removal_details['files_removed'])} file(s)/folder(s)"
    if removal_details['errors']:
        summary += f"\n{len(removal_details['errors'])} error(s) during removal"
    summary += "\n\nTip: docker system df"
    show_result_panel(summary, f"{container_name} Removed")

    input("\nPress Enter...")


def _get_container_images(container_name, compose_file=None):
    '''Get all Docker images used by a container BEFORE removal.
    Also finds leftover image tags from the same repository (e.g. after updates).
    Must be called before docker rm/compose down since inspect needs the container alive.'''
    images = set()
    repos = set()

    # 1. Inspect the main container
    result = safe_docker_run(
        ['docker', 'inspect', '--format', '{{.Config.Image}}', container_name],
        capture_output=True, text=True
    )
    if result and result.returncode == 0:
        img = result.stdout.strip()
        if img:
            images.add(img)
            # Extract repository (e.g. "n8nio/n8n:beta" -> "n8nio/n8n")
            repo = img.rsplit(':', 1)[0] if ':' in img else img
            if repo:
                repos.add(repo)

    # 2. Find all containers belonging to the same compose project
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={container_name}',
         '--format', '{{.Image}}'],
        capture_output=True, text=True
    )
    if result and result.returncode == 0:
        for img in result.stdout.strip().split('\n'):
            img = img.strip()
            if img:
                images.add(img)
                repo = img.rsplit(':', 1)[0] if ':' in img else img
                if repo:
                    repos.add(repo)

    # 3. Parse compose file for image directives as fallback
    if compose_file and os.path.exists(compose_file):
        try:
            import yaml
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            for service_config in compose_data.get('services', {}).values():
                img = service_config.get('image')
                if img:
                    images.add(img)
                    repo = img.rsplit(':', 1)[0] if ':' in img else img
                    if repo:
                        repos.add(repo)
        except Exception:
            pass

    # 4. Find ALL tags of the same repositories (catches leftover images from updates)
    if repos:
        result = safe_docker_run(
            ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
            capture_output=True, text=True
        )
        if result and result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                img_repo = line.rsplit(':', 1)[0] if ':' in line else line
                if img_repo in repos:
                    images.add(line)

    return list(images)


def _force_remove_container(container_name, removal_details):
    '''Force-remove a container if it still exists (running or stopped).'''
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
        capture_output=True, text=True
    )
    if result and result.returncode == 0 and container_name in result.stdout:
        remove_result = safe_docker_run(
            ['docker', 'rm', '-f', container_name],
            capture_output=True, text=True
        )
        if remove_result and remove_result.returncode == 0:
            show_step_detail(f"Container {container_name} removed")
        elif remove_result:
            removal_details['errors'].append(f"Container removal: {remove_result.stderr.strip()}")


def _remove_project_containers(container_name, removal_details):
    '''Remove orphaned containers from the same compose project (NOT intentional instances).
    Only removes containers that share the same compose project label.'''
    # Only remove containers that belong to the SAME compose project
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={container_name}',
         '--format', '{{.Names}}'],
        capture_output=True, text=True
    )
    if not result or result.returncode != 0:
        return

    for name in result.stdout.strip().split('\n'):
        name = name.strip()
        if not name or name == container_name:
            continue
        remove_result = safe_docker_run(
            ['docker', 'rm', '-f', name],
            capture_output=True, text=True
        )
        if remove_result and remove_result.returncode == 0:
            show_step_detail(f"Orphaned container {name} removed")


def _volume_belongs_to_instance(volume_name, container_name):
    '''Check if a Docker volume belongs to a specific instance'''
    if volume_name == container_name:
        return True
    if volume_name.startswith(f'{container_name}_'):
        return True
    return False