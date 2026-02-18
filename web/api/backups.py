import subprocess
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request
from web.auth import require_permission
from utils.validation import validate_filename, validate_container_name

bp = Blueprint('api_backups', __name__, url_prefix='/api')
BACKUP_DIR = Path(__file__).parent.parent.parent / 'backups'


def _get_meta_path(backup_path: Path) -> Path:
    name = backup_path.name
    for ext in ('.tar.gz', '.zip', '.sql', '.rdb'):
        if name.endswith(ext):
            stem = name[:-len(ext)]
            return backup_path.parent / f"{stem}.meta"
    return backup_path.with_suffix('.meta')


def _generic_volume_backup(container_name: str) -> bool:
    from utils.system import is_windows
    try:
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format',
             '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}\n{{end}}{{end}}'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False
        volumes = [v.strip() for v in result.stdout.strip().splitlines() if v.strip()]
        if not volumes:
            return False

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        volume_name = volumes[0]
        backup_dir_abs = str(BACKUP_DIR.resolve())

        if is_windows():
            backup_name = f"{container_name}_{timestamp}.zip"
            br = subprocess.run(
                ['docker', 'run', '--rm',
                 '-v', f'{volume_name}:/data:ro',
                 '-v', f'{backup_dir_abs}:/backup',
                 'alpine', 'sh', '-c',
                 f'apk add --no-cache zip -q && cd /data && zip -r /backup/{backup_name} .'],
                capture_output=True, text=True
            )
        else:
            backup_name = f"{container_name}_{timestamp}.tar.gz"
            br = subprocess.run(
                ['docker', 'run', '--rm',
                 '-v', f'{volume_name}:/data:ro',
                 '-v', f'{backup_dir_abs}:/backup',
                 'alpine', 'tar', 'czf', f'/backup/{backup_name}', '-C', '/data', '.'],
                capture_output=True, text=True
            )

        if br.returncode != 0:
            return False

        meta_path = _get_meta_path(BACKUP_DIR / backup_name)
        with open(meta_path, 'w') as f:
            f.write(f"container: {container_name}\n")
            f.write(f"app_type: generic\n")
            f.write(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"volume: {volume_name}\n")
        return True
    except Exception:
        return False


def _generic_volume_restore(container_name: str, backup_file: Path) -> bool:
    try:
        meta_path = _get_meta_path(backup_file)
        volume_name = None
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                for line in f:
                    if line.startswith('volume:'):
                        volume_name = line.split(':', 1)[1].strip()
                        break
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
            return False

        backup_dir_abs = str(BACKUP_DIR.resolve())
        backup_name = backup_file.name
        subprocess.run(['docker', 'stop', container_name], capture_output=True)

        if backup_name.endswith('.zip'):
            rr = subprocess.run(
                ['docker', 'run', '--rm',
                 '-v', f'{volume_name}:/data',
                 '-v', f'{backup_dir_abs}:/backup:ro',
                 'alpine', 'sh', '-c',
                 f'apk add --no-cache unzip -q && rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; unzip -o /backup/{backup_name} -d /data'],
                capture_output=True, text=True
            )
        elif backup_name.endswith('.tar.gz'):
            rr = subprocess.run(
                ['docker', 'run', '--rm',
                 '-v', f'{volume_name}:/data',
                 '-v', f'{backup_dir_abs}:/backup:ro',
                 'alpine', 'sh', '-c',
                 f'rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; tar xzf /backup/{backup_name} -C /data'],
                capture_output=True, text=True
            )
        else:
            subprocess.run(['docker', 'start', container_name], capture_output=True)
            return False

        subprocess.run(['docker', 'start', container_name], capture_output=True)
        return rr.returncode == 0
    except Exception:
        return False


def _require_pro():
    from license import get_license_manager
    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403
    return None


@bp.route('/backups')
@require_permission('backups.read')
def list_backups():
    blocked = _require_pro()
    if blocked:
        return blocked

    if not BACKUP_DIR.exists():
        return jsonify([])

    extensions = ['*.sql', '*.tar.gz', '*.zip', '*.rdb']
    backups = []
    for ext in extensions:
        backups.extend(BACKUP_DIR.glob(ext))

    result = []
    for backup in sorted(backups, key=lambda f: f.stat().st_mtime, reverse=True):
        meta = {}
        meta_file = _get_meta_path(backup)
        if meta_file.exists():
            try:
                lines = meta_file.read_text().splitlines()
                for line in lines:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key = key.strip().lower()
                        if key == 'container':
                            meta['container'] = val.strip()
                        elif key in ('type', 'app_type'):
                            meta['type'] = val.strip()
                        elif key in ('timestamp', 'created'):
                            meta['timestamp'] = val.strip()[:19]
            except Exception:
                pass

        result.append({
            'filename': backup.name,
            'size': backup.stat().st_size,
            'meta': meta
        })

    return jsonify(result)


@bp.route('/backups/create', methods=['POST'])
@require_permission('backups.create')
def create_backup():
    blocked = _require_pro()
    if blocked:
        return blocked

    container_name = request.json.get('container_name')
    if not container_name:
        return jsonify({'success': False, 'message': 'container_name required'}), 400

    try:
        container_name = validate_container_name(container_name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    from apps.manifest_loader import load_all_manifests
    from apps.hook_loader import get_hook_loader

    manifests = load_all_manifests()
    hook_loader = get_hook_loader()

    # Try to match container to manifest
    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    base_name = base_name.split('-')[0] if '-' in base_name else base_name
    manifest = manifests.get(base_name)

    if manifest and hook_loader.has_hook(manifest, 'backup'):
        try:
            success = hook_loader.execute_hook(manifest, 'backup', container_name)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Backup error: {str(e)}'}), 500
    else:
        # Generic volume backup fallback
        success = _generic_volume_backup(container_name)

    if success:
        try:
            from license import get_license_manager
            from license.audit_logger import get_audit_logger, AuditEventType
            lm = get_license_manager()
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.BACKUP, container_name, {'source': 'web_ui'})
        except Exception:
            pass
        return jsonify({'success': True, 'message': f'Backup created for {container_name}'})
    return jsonify({'success': False, 'message': 'Backup failed'}), 500


@bp.route('/backups/restore', methods=['POST'])
@require_permission('backups.restore')
def restore_backup():
    blocked = _require_pro()
    if blocked:
        return blocked

    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': 'filename required'}), 400

    try:
        filename = validate_filename(filename, allowed_extensions={'sql', 'tar.gz', 'zip', 'rdb'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    backup_file = BACKUP_DIR / filename
    # Ensure resolved path stays within BACKUP_DIR
    if not str(backup_file.resolve()).startswith(str(BACKUP_DIR.resolve())):
        return jsonify({'success': False, 'message': 'Invalid file path'}), 400

    if not backup_file.exists():
        return jsonify({'success': False, 'message': 'Backup file not found'}), 404

    # Read metadata
    meta_file = _get_meta_path(backup_file)
    if not meta_file.exists():
        return jsonify({'success': False, 'message': 'Metadata file not found'}), 404

    container_name = None
    app_type = None
    try:
        lines = meta_file.read_text().splitlines()
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().lower()
                if key == 'container':
                    container_name = val.strip()
                elif key in ('type', 'app_type'):
                    app_type = val.strip()
    except Exception:
        return jsonify({'success': False, 'message': 'Cannot read metadata'}), 500

    if not container_name:
        return jsonify({'success': False, 'message': 'No container info in metadata'}), 400

    from apps.manifest_loader import load_all_manifests
    from apps.hook_loader import get_hook_loader

    manifests = load_all_manifests()
    hook_loader = get_hook_loader()

    base_name = container_name.split('_')[0] if '_' in container_name else container_name
    manifest = manifests.get(base_name) or manifests.get(app_type)

    if manifest and hook_loader.has_hook(manifest, 'restore'):
        try:
            success = hook_loader.execute_hook(manifest, 'restore', backup_file, container_name)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Restore error: {str(e)}'}), 500
    else:
        # Generic volume restore fallback
        success = _generic_volume_restore(container_name, backup_file)

    if success:
        try:
            from license import get_license_manager
            from license.audit_logger import get_audit_logger, AuditEventType
            lm = get_license_manager()
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.RESTORE, container_name, {
                'backup_file': filename, 'source': 'web_ui'
            })
        except Exception:
            pass
        return jsonify({'success': True, 'message': f'Backup restored for {container_name}'})
    return jsonify({'success': False, 'message': 'Restore failed'}), 500


@bp.route('/backups/delete', methods=['POST'])
@require_permission('backups.delete')
def delete_backup():
    blocked = _require_pro()
    if blocked:
        return blocked

    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': 'filename required'}), 400

    try:
        filename = validate_filename(filename, allowed_extensions={'sql', 'tar.gz', 'zip', 'rdb'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    backup_file = BACKUP_DIR / filename
    if not str(backup_file.resolve()).startswith(str(BACKUP_DIR.resolve())):
        return jsonify({'success': False, 'message': 'Invalid file path'}), 400

    if not backup_file.exists():
        return jsonify({'success': False, 'message': 'Backup not found'}), 404

    try:
        backup_file.unlink()
        meta_file = _get_meta_path(backup_file)
        if meta_file.exists():
            meta_file.unlink()
        return jsonify({'success': True, 'message': f'Backup {filename} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete error: {str(e)}'}), 500
