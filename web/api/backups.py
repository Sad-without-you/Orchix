from pathlib import Path
from flask import Blueprint, jsonify, request
from web.auth import login_required
from utils.validation import validate_filename, validate_container_name

bp = Blueprint('api_backups', __name__, url_prefix='/api')
BACKUP_DIR = Path(__file__).parent.parent.parent / 'backups'


def _require_pro():
    from license import get_license_manager
    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403
    return None


@bp.route('/backups')
@login_required
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
        meta_file = backup.with_suffix('.meta')
        if meta_file.exists():
            try:
                lines = meta_file.read_text().splitlines()
                for line in lines:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key = key.strip().lower()
                        if key == 'container':
                            meta['container'] = val.strip()
                        elif key == 'type':
                            meta['type'] = val.strip()
                        elif key == 'timestamp':
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
@login_required
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
            if success:
                # Audit log
                try:
                    from license import get_license_manager
                    from license.audit_logger import get_audit_logger, AuditEventType
                    lm = get_license_manager()
                    logger = get_audit_logger(enabled=lm.is_pro())
                    logger.log_event(AuditEventType.BACKUP, container_name, {'source': 'web_ui'})
                except Exception:
                    pass
                return jsonify({'success': True, 'message': f'Backup created for {container_name}'})
            return jsonify({'success': False, 'message': 'Backup hook returned failure'}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': f'Backup error: {str(e)}'}), 500

    return jsonify({'success': False, 'message': f'No backup hook available for {base_name}'}), 400


@bp.route('/backups/restore', methods=['POST'])
@login_required
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
    meta_file = backup_file.with_suffix('.meta')
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
                elif key == 'type':
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

    if not manifest or not hook_loader.has_hook(manifest, 'restore'):
        return jsonify({'success': False, 'message': 'No restore hook available'}), 400

    try:
        success = hook_loader.execute_hook(manifest, 'restore', backup_file, container_name)
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
    except Exception as e:
        return jsonify({'success': False, 'message': f'Restore error: {str(e)}'}), 500


@bp.route('/backups/delete', methods=['POST'])
@login_required
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
        meta_file = backup_file.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
        return jsonify({'success': True, 'message': f'Backup {filename} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete error: {str(e)}'}), 500
