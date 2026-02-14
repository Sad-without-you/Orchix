import json
import logging
import shutil
import tarfile
import socket
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request
from web.auth import require_permission
from utils.validation import validate_container_name

_log = logging.getLogger(__name__)

bp = Blueprint('api_migration', __name__, url_prefix='/api')
MIGRATION_DIR = Path(__file__).parent.parent.parent / 'migrations'
BACKUP_DIR = Path(__file__).parent.parent.parent / 'backups'


def _safe_tar_extract(tar, path):
    """Extract tar safely, blocking path traversal attacks."""
    target = Path(path).resolve()
    for member in tar.getmembers():
        if member.name.startswith('/') or '..' in member.name:
            raise ValueError(f"Unsafe path in archive: {member.name}")
        member_path = (target / member.name).resolve()
        if not str(member_path).startswith(str(target)):
            raise ValueError(f"Path traversal detected: {member.name}")
    tar.extractall(path)


def _require_pro():
    from license import get_license_manager
    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403
    return None


@bp.route('/migrations')
@require_permission('migration.read')
def list_migrations():
    blocked = _require_pro()
    if blocked:
        return blocked

    MIGRATION_DIR.mkdir(exist_ok=True)
    packages = list(MIGRATION_DIR.glob("orchix_migration_*.tar.gz"))

    result = []
    for pkg in sorted(packages, key=lambda f: f.stat().st_mtime, reverse=True):
        size = pkg.stat().st_size
        created = datetime.fromtimestamp(pkg.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

        # Try to read manifest info
        info = {'containers': 0, 'source': 'unknown', 'target_platform': 'unknown'}
        try:
            with tarfile.open(pkg, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.name.endswith('migration_manifest.json'):
                        f = tar.extractfile(member)
                        if f:
                            data = json.loads(f.read().decode('utf-8'))
                            info['containers'] = len(data.get('containers', []))
                            info['source'] = data.get('source_hostname', 'unknown')
                            info['target_platform'] = data.get('target_platform', 'unknown')
                        break
        except Exception:
            pass

        result.append({
            'filename': pkg.name,
            'size': size,
            'created': created,
            'containers': info['containers'],
            'source': info['source'],
            'target_platform': info['target_platform'],
        })

    return jsonify(result)


@bp.route('/migrations/containers')
@require_permission('migration.read')
def get_orchix_containers():
    """Get ORCHIX-managed containers (those with compose files)."""
    blocked = _require_pro()
    if blocked:
        return blocked

    from cli.migration_menu import get_all_orchix_containers
    containers = get_all_orchix_containers()
    return jsonify(containers)


@bp.route('/migrations/export', methods=['POST'])
@require_permission('migration.export')
def export_migration():
    blocked = _require_pro()
    if blocked:
        return blocked

    containers = request.json.get('containers', [])
    target_platform = request.json.get('target_platform', 'linux')

    if not containers:
        return jsonify({'success': False, 'message': 'No containers selected'}), 400

    # Validate all container names
    for i, name in enumerate(containers):
        try:
            containers[i] = validate_container_name(name)
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400

    if target_platform not in ('linux', 'windows'):
        return jsonify({'success': False, 'message': 'Invalid target platform'}), 400

    MIGRATION_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"orchix_migration_{timestamp}"
    package_dir = MIGRATION_DIR / package_name
    package_dir.mkdir(exist_ok=True)

    target_is_windows = target_platform == 'windows'

    migration_data = {
        'version': '2.0.0',
        'timestamp': timestamp,
        'source_hostname': socket.gethostname(),
        'target_platform': target_platform,
        'containers': []
    }

    for container_name in containers:
        container_data = {
            'name': container_name,
            'compose_file': f'docker-compose-{container_name}.yml',
            'backup_file': None
        }

        # Copy compose file
        compose_src = Path(f'docker-compose-{container_name}.yml')
        if compose_src.exists():
            shutil.copy2(compose_src, package_dir / compose_src.name)

        # Create backup
        try:
            from cli.migration_menu import _create_container_backup
            backup_file = _create_container_backup(container_name, package_dir, target_is_windows)
            if backup_file:
                container_data['backup_file'] = backup_file
        except Exception:
            pass

        migration_data['containers'].append(container_data)

    # Write manifest
    manifest_file = package_dir / 'migration_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(migration_data, f, indent=2)

    # Create tarball
    tarball_path = MIGRATION_DIR / f"{package_name}.tar.gz"
    with tarfile.open(tarball_path, 'w:gz') as tar:
        tar.add(package_dir, arcname=package_name)

    shutil.rmtree(package_dir)

    size = tarball_path.stat().st_size

    return jsonify({
        'success': True,
        'message': f'Migration package created ({len(containers)} containers)',
        'filename': tarball_path.name,
        'size': size
    })


@bp.route('/migrations/import', methods=['POST'])
@require_permission('migration.import')
def import_migration():
    blocked = _require_pro()
    if blocked:
        return blocked

    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': 'filename required'}), 400

    # Validate filename: must match orchix_migration_*.tar.gz pattern
    import re
    if not re.match(r'^orchix_migration_\d{8}_\d{6}\.tar\.gz$', filename):
        return jsonify({'success': False, 'message': 'Invalid filename format'}), 400

    package_path = MIGRATION_DIR / filename
    if not str(package_path.resolve()).startswith(str(MIGRATION_DIR.resolve())):
        return jsonify({'success': False, 'message': 'Invalid file path'}), 400
    if not package_path.exists():
        return jsonify({'success': False, 'message': 'Package not found'}), 404

    # Extract with path traversal protection
    extract_dir = MIGRATION_DIR / filename.replace('.tar.gz', '')
    try:
        with tarfile.open(package_path, 'r:gz') as tar:
            _safe_tar_extract(tar, MIGRATION_DIR)
    except ValueError as e:
        _log.warning(f"Blocked malicious archive: {e}")
        return jsonify({'success': False, 'message': 'Archive contains unsafe paths'}), 400
    except Exception as e:
        _log.error(f"Extract failed: {e}")
        return jsonify({'success': False, 'message': 'Failed to extract package'}), 500

    # Read manifest
    manifest_file = extract_dir / 'migration_manifest.json'
    if not manifest_file.exists():
        shutil.rmtree(extract_dir)
        return jsonify({'success': False, 'message': 'Invalid package (no manifest)'}), 400

    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest_data = json.load(f)

    from apps.manifest_loader import load_all_manifests
    from apps.hook_loader import get_hook_loader
    from utils.docker_utils import safe_docker_run

    manifests = load_all_manifests()
    hook_loader = get_hook_loader()
    BACKUP_DIR.mkdir(exist_ok=True)

    results = []
    for container_data in manifest_data.get('containers', []):
        container_name = container_data.get('name')

        # Validate container name from manifest
        try:
            container_name = validate_container_name(container_name)
        except (ValueError, TypeError):
            results.append({'name': container_name, 'success': False, 'message': 'Invalid container name'})
            continue

        status = {'name': container_name, 'success': False, 'message': ''}

        # Check if exists
        r = safe_docker_run(
            ['docker', 'ps', '-a', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
            capture_output=True, text=True
        )
        if r and container_name in r.stdout:
            status['message'] = 'Container already exists - skipped'
            results.append(status)
            continue

        # Copy compose file
        compose_file = container_data.get('compose_file')
        if compose_file:
            compose_src = extract_dir / compose_file
            if compose_src.exists():
                shutil.copy2(compose_src, Path(compose_file))

        # Deploy container
        if compose_file:
            r = safe_docker_run(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                capture_output=True, text=True
            )
            if not r or r.returncode != 0:
                status['message'] = 'Failed to start container'
                results.append(status)
                continue

        # Restore backup
        backup_file = container_data.get('backup_file')
        if backup_file:
            backup_src = extract_dir / backup_file
            backup_dst = BACKUP_DIR / backup_file
            if backup_src.exists():
                shutil.copy2(backup_src, backup_dst)

                # Copy meta file
                from cli.migration_menu import _get_meta_file
                meta_src = _get_meta_file(backup_src)
                if meta_src.exists():
                    meta_dst = _get_meta_file(backup_dst)
                    shutil.copy2(meta_src, meta_dst)

                # Restore via hooks
                base_name = container_name.split('_')[0] if '_' in container_name else container_name
                manifest = manifests.get(base_name)
                if manifest and hook_loader.has_hook(manifest, 'restore'):
                    try:
                        hook_loader.execute_hook(manifest, 'restore', backup_dst, container_name)
                    except Exception:
                        pass

        status['success'] = True
        status['message'] = 'Imported successfully'
        results.append(status)

    shutil.rmtree(extract_dir)

    success_count = sum(1 for r in results if r['success'])
    return jsonify({
        'success': True,
        'message': f'Imported {success_count}/{len(results)} containers',
        'results': results
    })
