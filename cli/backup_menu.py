import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

_ORCHIX_ROOT = Path(__file__).parent.parent
BACKUP_DIR = _ORCHIX_ROOT / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)


def _alpine_image_exists() -> bool:
    return subprocess.run(['docker', 'image', 'inspect', 'alpine'],
                         capture_output=True).returncode == 0


def _get_meta_path(backup_path: Path) -> Path:
    name = backup_path.name
    for ext in ('.tar.gz', '.zip', '.sql', '.rdb'):
        if name.endswith(ext):
            stem = name[:-len(ext)]
            return backup_path.parent / f"{stem}.meta"
    return backup_path.with_suffix('.meta')


def _get_compose_sidecar_path(backup_path: Path) -> Path:
    name = backup_path.name
    for ext in ('.tar.gz', '.zip', '.sql', '.rdb'):
        if name.endswith(ext):
            stem = name[:-len(ext)]
            return backup_path.parent / f"{stem}.compose.yml"
    return backup_path.with_suffix('.compose.yml')


def _start_container(container_name: str, compose_file: Path):
    """Start container via compose if available (preserves env vars), else via docker start."""
    if compose_file.exists():
        from utils.docker_utils import ensure_orchix_network
        ensure_orchix_network()
        subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
            capture_output=True
        )
    else:
        subprocess.run(['docker', 'start', container_name], capture_output=True)


def _generic_volume_backup(container_name: str) -> bool:
    from utils.system import is_windows
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format',
             '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}\n{{end}}{{end}}'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            show_warning("Could not inspect container volumes")
            return False

        volumes = [v.strip() for v in result.stdout.strip().splitlines() if v.strip()]
        if not volumes:
            show_warning("No named volumes found for this container")
            return False

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir_abs = str(BACKUP_DIR.resolve())
        alpine_existed = _alpine_image_exists()

        # Stop container for a consistent backup
        subprocess.run(['docker', 'stop', container_name], capture_output=True)

        # Build volume mounts and copy commands for all volumes
        vol_mounts = []
        for vol in volumes:
            vol_mounts += ['-v', f'{vol}:/_vol_{vol}:ro']

        stat_cmds = '; '.join(
            f'stat -c %u /_vol_{vol} 2>/dev/null || echo 0' for vol in volumes
        )

        if is_windows():
            backup_name = f"{container_name}_{timestamp}.zip"
            if len(volumes) == 1:
                copy_cmd = (f'{stat_cmds}; '
                            f'apk add --no-cache zip -q && cd /_vol_{volumes[0]} && zip -r /backup/{backup_name} .')
            else:
                mkdir_cmds = ' && '.join(
                    f'mkdir -p /tmp/bk/{vol} && cp -a /_vol_{vol}/. /tmp/bk/{vol}/' for vol in volumes
                )
                copy_cmd = (f'{stat_cmds}; '
                            f'apk add --no-cache zip -q && mkdir -p /tmp/bk && {mkdir_cmds} && cd /tmp/bk && zip -r /backup/{backup_name} .')
            backup_result = subprocess.run(
                ['docker', 'run', '--rm'] + vol_mounts + ['-v', f'{backup_dir_abs}:/backup',
                 'alpine', 'sh', '-c', copy_cmd],
                capture_output=True, text=True
            )
        else:
            backup_name = f"{container_name}_{timestamp}.tar.gz"
            if len(volumes) == 1:
                tar_cmd = (f'{stat_cmds}; '
                           f'tar czf /backup/{backup_name} -C /_vol_{volumes[0]} .')
            else:
                mkdir_cmds = ' && '.join(
                    f'mkdir -p /tmp/bk/{vol} && cp -a /_vol_{vol}/. /tmp/bk/{vol}/' for vol in volumes
                )
                tar_cmd = (f'{stat_cmds}; '
                           f'mkdir -p /tmp/bk && {mkdir_cmds} && tar czf /backup/{backup_name} -C /tmp/bk .')
            backup_result = subprocess.run(
                ['docker', 'run', '--rm'] + vol_mounts + ['-v', f'{backup_dir_abs}:/backup',
                 'alpine', 'sh', '-c', tar_cmd],
                capture_output=True, text=True
            )

        # Parse UIDs from stdout (one per line, digits only)
        volume_uids = []
        if backup_result.stdout:
            volume_uids = [l.strip() for l in backup_result.stdout.splitlines()
                           if l.strip().isdigit()][:len(volumes)]

        if not alpine_existed:
            subprocess.run(['docker', 'rmi', 'alpine'], capture_output=True)

        # Restart container regardless of backup result
        subprocess.run(['docker', 'start', container_name], capture_output=True)

        if backup_result.returncode != 0:
            show_warning("Volume backup command failed")
            return False

        # Write meta file
        meta_path = _get_meta_path(BACKUP_DIR / backup_name)
        with open(meta_path, 'w') as f:
            f.write(f"container: {container_name}\n")
            f.write(f"app_type: generic\n")
            f.write(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if len(volumes) == 1:
                f.write(f"volume: {volumes[0]}\n")
            else:
                f.write(f"volumes: {','.join(volumes)}\n")
            if volume_uids:
                pairs = ','.join(f'{v}:{u}' for v, u in zip(volumes, volume_uids))
                f.write(f"volume_owners: {pairs}\n")

        # Also back up the compose file so restore can recreate the container exactly
        compose_src = _ORCHIX_ROOT / f"docker-compose-{container_name}.yml"
        if compose_src.exists():
            shutil.copy2(compose_src, _get_compose_sidecar_path(BACKUP_DIR / backup_name))

        return True

    except Exception as e:
        show_warning(f"Backup error: {e}")
        return False


def _generic_volume_restore(container_name: str, backup_file: Path) -> bool:
    try:
        meta_path = _get_meta_path(backup_file)
        volume_name = None
        all_volumes = []  # multi-volume format
        volume_owners = {}  # vol -> uid string
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                for line in f:
                    if line.startswith('volumes:'):
                        all_volumes = [v.strip() for v in line.split(':', 1)[1].strip().split(',') if v.strip()]
                        volume_name = all_volumes[0] if all_volumes else None
                    elif line.startswith('volume:'):
                        volume_name = line.split(':', 1)[1].strip()
                    elif line.startswith('volume_owners:'):
                        for pair in line.split(':', 1)[1].strip().split(','):
                            kv = pair.strip().rsplit(':', 1)
                            if len(kv) == 2 and kv[1].strip().isdigit():
                                volume_owners[kv[0].strip()] = kv[1].strip()

        if not volume_name:
            result = subprocess.run(
                ['docker', 'inspect', container_name, '--format',
                 '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}\n{{end}}{{end}}'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                vols = [v.strip() for v in result.stdout.strip().splitlines() if v.strip()]
                if vols:
                    volume_name = vols[0]

        if not volume_name:
            # Try manifest before falling back to a generic name
            from apps.manifest_loader import load_all_manifests
            _manifests = load_all_manifests()
            _base = container_name.split('_')[0] if '_' in container_name else container_name
            _manifest = _manifests.get(_base)
            if _manifest and _manifest.get('volumes'):
                _first = _manifest['volumes'][0]
                if _first.get('name_suffix'):
                    volume_name = f"{container_name}_{_first['name_suffix']}"
        if not volume_name:
            volume_name = f"{container_name}_data"

        backup_dir_abs = str(BACKUP_DIR.resolve())
        backup_name = backup_file.name
        alpine_existed = _alpine_image_exists()
        compose_dest = _ORCHIX_ROOT / f"docker-compose-{container_name}.yml"
        is_multi = len(all_volumes) > 1

        # Stop container before modifying its volume
        subprocess.run(['docker', 'stop', container_name], capture_output=True)

        # Fallback: if no volume_owners in meta, resolve UID from image (handles old backups)
        if not volume_owners:
            from utils.docker_utils import resolve_container_uid
            fallback_uid = resolve_container_uid(container_name)
            if fallback_uid != '0':
                vols_to_fix = all_volumes if len(all_volumes) > 1 else [volume_name]
                for vol in vols_to_fix:
                    if vol:
                        volume_owners[vol] = fallback_uid

        # Restore compose file from sidecar so container config (env vars, ports) matches
        compose_sidecar = _get_compose_sidecar_path(backup_file)
        if compose_sidecar.exists():
            shutil.copy2(compose_sidecar, compose_dest)

        def _restore_single(vol: str, subdir: str | None) -> subprocess.CompletedProcess:
            """Restore one volume, optionally extracting only a named subdir."""
            uid = volume_owners.get(vol, '0')
            chown_cmd = f' && chown -R {uid}:{uid} /data' if uid and uid != '0' else ''
            if backup_name.endswith('.zip'):
                if subdir:
                    cmd = (f'apk add --no-cache unzip -q && rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; '
                           f'unzip -o /backup/{backup_name} "{subdir}/*" -d /tmp/x && '
                           f'cp -a /tmp/x/{subdir}/. /data/' + chown_cmd)
                else:
                    cmd = (f'apk add --no-cache unzip -q && rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; '
                           f'unzip -o /backup/{backup_name} -d /data' + chown_cmd)
                return subprocess.run(
                    ['docker', 'run', '--rm',
                     '-v', f'{vol}:/data',
                     '-v', f'{backup_dir_abs}:/backup:ro',
                     'alpine', 'sh', '-c', cmd],
                    capture_output=True, text=True
                )
            elif backup_name.endswith('.tar.gz'):
                if subdir:
                    cmd = (f'rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; '
                           f'tar xzf /backup/{backup_name} -C /data --strip-components=1 {subdir}' + chown_cmd)
                else:
                    cmd = (f'rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; '
                           f'tar xzf /backup/{backup_name} -C /data' + chown_cmd)
                return subprocess.run(
                    ['docker', 'run', '--rm',
                     '-v', f'{vol}:/data',
                     '-v', f'{backup_dir_abs}:/backup:ro',
                     'alpine', 'sh', '-c', cmd],
                    capture_output=True, text=True
                )
            return None

        if is_multi:
            restore_result = None
            for vol in all_volumes:
                r = _restore_single(vol, vol)
                if r is not None and r.returncode != 0:
                    restore_result = r
                    break
        else:
            restore_result = _restore_single(volume_name, None)

        if not alpine_existed:
            subprocess.run(['docker', 'rmi', 'alpine'], capture_output=True)

        if restore_result is not None and restore_result.returncode != 0:
            show_warning(f"Restore command failed: {restore_result.stderr[:200]}")
            _start_container(container_name, compose_dest)
            return False

        # Start container via compose (picks up correct env vars like encryption keys)
        _start_container(container_name, compose_dest)
        return True

    except Exception as e:
        show_warning(f"Restore error: {e}")
        return False


def show_backup_menu():
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
    show_panel("Create Backup", "Select container to backup")

    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
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

    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()

    choices = []
    container_manifest_map = {}

    for container in containers:
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

    choice = select_from_list("Select container to backup", choices)

    if "Cancel" in choice:
        return

    container_name = None
    for container in containers:
        if container in choice:
            container_name = container
            break

    if not container_name:
        show_error("Invalid selection")
        input("Press Enter...")
        return

    manifest = container_manifest_map.get(container_name)

    print()
    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Creating backup for {container_name}...", total=100)

        if manifest:
            from apps.hook_loader import get_hook_loader
            hook_loader = get_hook_loader()
            if hook_loader.has_hook(manifest, 'backup'):
                success = hook_loader.execute_hook(manifest, 'backup', container_name)
            else:
                success = _generic_volume_backup(container_name)
        else:
            success = _generic_volume_backup(container_name)

        progress.update(task, completed=100, description="Backup complete!" if success else "Backup failed!")

    if not success:
        show_error("Backup failed!")

    print()
    input("Press Enter...")


def restore_backup_menu():
    show_panel("Restore from Backup", "Select app to restore")

    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))

    if not backups:
        show_warning("No backups found!")
        input("Press Enter...")
        return

    apps_with_backups = {}

    for backup in backups:
        meta_file = _get_meta_path(backup)
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                container = lines[0].split(':')[1].strip()
                app_type = lines[1].split(':')[1].strip()

                if container not in apps_with_backups:
                    apps_with_backups[container] = {'type': app_type, 'backups': []}

                apps_with_backups[container]['backups'].append(backup)

    if not apps_with_backups:
        show_warning("No valid backups found!")
        input("Press Enter...")
        return

    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()

    app_choices = []
    for container, info in sorted(apps_with_backups.items()):
        app_type = info['type']
        count = len(info['backups'])

        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name) or manifests.get(app_type)
        icon = manifest.get('icon', '📦') if manifest else '📦'

        app_choices.append(f"{icon} {container} ({count} backups)")

    app_choices.append("⬅️  Cancel")

    selected_app = select_from_list("Select app to restore", app_choices)

    if "Cancel" in selected_app:
        return

    container_name = selected_app.split(' ')[1]

    app_backups = apps_with_backups[container_name]['backups']

    backup_choices = []
    for backup in sorted(app_backups, reverse=True):
        meta_file = _get_meta_path(backup)
        timestamp = 'Unknown'
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                timestamp = lines[2].split(':', 1)[1].strip()[:19] if len(lines) > 2 else 'Unknown'
        backup_choices.append(f"{timestamp} - {backup.name}")

    backup_choices.append("⬅️  Cancel")

    selected_backup_choice = select_from_list(
        f"Select backup for {container_name}",
        backup_choices
    )

    if "Cancel" in selected_backup_choice:
        return

    backup_name = selected_backup_choice.split(' - ')[1]
    selected_backup = BACKUP_DIR / backup_name

    meta_file = _get_meta_path(selected_backup)
    if not meta_file.exists():
        show_error("Metadata file not found!")
        input("Press Enter...")
        return

    with open(meta_file, 'r') as f:
        lines = f.readlines()
        container_name = lines[0].split(':')[1].strip()
        app_type = lines[1].split(':')[1].strip()

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

    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    manifest = manifests.get(base_name) or manifests.get(app_type)

    print()
    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Restoring {container_name}...", total=100)

        if manifest:
            from apps.hook_loader import get_hook_loader
            hook_loader = get_hook_loader()
            if hook_loader.has_hook(manifest, 'restore'):
                success = hook_loader.execute_hook(manifest, 'restore', selected_backup, container_name)
            else:
                success = _generic_volume_restore(container_name, selected_backup)
        else:
            success = _generic_volume_restore(container_name, selected_backup)

        progress.update(task, completed=100, description="Restore complete!" if success else "Restore failed!")

    if not success:
        show_error("Restore failed!")

    print()
    input("Press Enter...")


def list_backups():
    show_info("Loading backups...")
    print()

    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))

    if not backups:
        show_warning("No backups found!")
    else:
        from apps.manifest_loader import load_all_manifests
        manifests = load_all_manifests()

        table = Table(title="📋 Available Backups", show_header=True, header_style="bold cyan")
        table.add_column("Container", style="cyan", width=20)
        table.add_column("Type", style="white", width=15)
        table.add_column("Format", style="dim", width=10)
        table.add_column("Date", style="white", width=20)
        table.add_column("File", style="dim", width=30)

        for backup in sorted(backups, reverse=True):
            meta_file = _get_meta_path(backup)
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    lines = f.readlines()
                    container = lines[0].split(':', 1)[1].strip()
                    app_type = lines[1].split(':', 1)[1].strip()
                    timestamp = lines[2].split(':', 1)[1].strip()[:19]

                    base_name = container.split('_')[0] if '_' in container else container
                    manifest = manifests.get(base_name) or manifests.get(app_type)

                    if manifest:
                        icon = manifest.get('icon', '📦').replace('\ufe0f', '')
                        type_display = f"{icon} {manifest['display_name']}"
                    else:
                        type_display = f"📦 {app_type}"

                    if backup.name.endswith('.zip'):
                        format_display = "📦 ZIP"
                    elif backup.name.endswith('.tar.gz'):
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
    show_panel("Delete Backup", "Select app")

    backups = list(BACKUP_DIR.glob("*.sql")) + \
              list(BACKUP_DIR.glob("*.tar.gz")) + \
              list(BACKUP_DIR.glob("*.zip")) + \
              list(BACKUP_DIR.glob("*.rdb"))

    if not backups:
        show_warning("No backups found!")
        input("Press Enter...")
        return

    apps_with_backups = {}

    for backup in backups:
        meta_file = _get_meta_path(backup)
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                container = lines[0].split(':')[1].strip()
                app_type = lines[1].split(':')[1].strip()

                if container not in apps_with_backups:
                    apps_with_backups[container] = {'type': app_type, 'backups': []}

                apps_with_backups[container]['backups'].append(backup)

    if not apps_with_backups:
        show_warning("No valid backups found!")
        input("Press Enter...")
        return

    from apps.manifest_loader import load_all_manifests
    manifests = load_all_manifests()

    app_choices = []
    for container, info in sorted(apps_with_backups.items()):
        app_type = info['type']
        count = len(info['backups'])

        base_name = container.split('_')[0] if '_' in container else container
        manifest = manifests.get(base_name) or manifests.get(app_type)
        icon = manifest.get('icon', '📦') if manifest else '📦'

        app_choices.append(f"{icon} {container} ({count} backups)")

    app_choices.append("⬅️  Cancel")

    selected_app = select_from_list("Select app", app_choices)

    if "Cancel" in selected_app:
        return

    container_name = selected_app.split(' ')[1]

    app_backups = apps_with_backups[container_name]['backups']

    backup_choices = []
    for backup in sorted(app_backups, reverse=True):
        meta_file = _get_meta_path(backup)
        timestamp = 'Unknown'
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                lines = f.readlines()
                timestamp = lines[2].split(':', 1)[1].strip()[:19] if len(lines) > 2 else 'Unknown'
        backup_choices.append(f"{timestamp} - {backup.name}")

    backup_choices.append("⬅️  Cancel")

    selected_backup_choice = select_from_list(
        "Select backup to delete",
        backup_choices
    )

    if "Cancel" in selected_backup_choice:
        return

    backup_name = selected_backup_choice.split(' - ')[1]
    selected_backup = BACKUP_DIR / backup_name

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

    with Progress(
        TextColumn("  │     [progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Deleting {backup_name}...", total=100)
        try:
            selected_backup.unlink()
            meta_file = _get_meta_path(selected_backup)
            if meta_file.exists():
                meta_file.unlink()
            compose_sidecar = _get_compose_sidecar_path(selected_backup)
            if compose_sidecar.exists():
                compose_sidecar.unlink()
            success = True
            err = None
        except Exception as e:
            success = False
            err = str(e)
        progress.update(task, completed=100, description="Deleted!" if success else "Delete failed!")

    if not success:
        show_error(f"Failed to delete backup: {err}")

    print()
    input("Press Enter...")
