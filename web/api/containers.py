import json as json_mod
import os
import shutil
from pathlib import Path
from flask import Blueprint, jsonify, request
from flask import session as flask_session
from web.auth import require_permission
from utils.docker_utils import safe_docker_run
from utils.validation import validate_container_name

bp = Blueprint('api_containers', __name__, url_prefix='/api')


def _log_audit(event_type, app_name, details=None):
    try:
        from license import get_license_manager
        from license.audit_logger import get_audit_logger, AuditEventType
        lm = get_license_manager()
        logger = get_audit_logger(enabled=lm.is_pro())
        logger.set_web_user(flask_session.get('username', 'unknown'))
        logger.log_event(AuditEventType[event_type], app_name, details or {'source': 'web_ui'})
    except Exception:
        pass


def _get_visible_container_names():
    """Get list of container names visible to current tier."""
    from cli.container_menu import get_visible_containers
    containers, _ = get_visible_containers()
    return containers


@bp.route('/containers')
@require_permission('containers.read')
def list_containers():
    from cli.container_menu import get_container_status

    containers = _get_visible_container_names()
    result = []

    # Try to get sizes (optional, may be slow)
    sizes = {}
    try:
        size_result = safe_docker_run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Size}}'],
            capture_output=True, text=True, timeout=10
        )
        if size_result and size_result.returncode == 0:
            import re
            for line in size_result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|', 1)
                    raw_size = parts[1].strip()
                    virtual_match = re.search(r'virtual\s+([\d.]+\s*[kKMGT]?B)', raw_size)
                    if virtual_match:
                        sizes[parts[0].strip()] = virtual_match.group(1)
                    else:
                        sizes[parts[0].strip()] = raw_size.split('(')[0].strip()
    except Exception:
        pass

    for name in containers:
        status = get_container_status(name)
        result.append({
            'name': name,
            'status': status,
            'size': sizes.get(name, '')
        })
    return jsonify(result)


@bp.route('/containers/selection-needed')
@require_permission('containers.read')
def selection_needed():  # Any authenticated user can check status
    """Check if container selection is needed (FREE tier with >limit containers)."""
    from license import get_license_manager
    lm = get_license_manager()
    needed = lm.needs_container_selection()
    return jsonify({
        'needed': needed,
        'limit': lm.get_container_limit()
    })


@bp.route('/containers/all-for-selection')
@require_permission('users.edit')
def all_for_selection():
    """Get ALL containers for selection UI (only when selection is needed)."""
    from license import get_license_manager
    from cli.container_menu import get_all_containers, get_container_status
    lm = get_license_manager()

    if not lm.needs_container_selection():
        return jsonify({'containers': [], 'message': 'Selection not needed'}), 400

    containers = get_all_containers()
    result = []
    for name in containers:
        status = get_container_status(name)
        result.append({'name': name, 'status': status})
    return jsonify({
        'containers': result,
        'limit': lm.get_container_limit()
    })


@bp.route('/containers/select', methods=['POST'])
@require_permission('users.edit')
def select_containers():
    """Save container selection for FREE tier. Admin only."""
    from license import get_license_manager
    from cli.container_menu import get_all_containers
    lm = get_license_manager()

    if lm.is_pro():
        return jsonify({'success': False, 'message': 'PRO users manage all containers'}), 400

    data = request.get_json()
    if not data or not isinstance(data.get('selected'), list):
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    selected = data['selected']

    # Validate all items are strings
    if not all(isinstance(n, str) and n.strip() for n in selected):
        return jsonify({'success': False, 'message': 'Invalid container names'}), 400

    selected = [n.strip() for n in selected]

    if not selected:
        return jsonify({'success': False, 'message': 'Select at least one container'}), 400

    limit = lm.get_container_limit()
    if len(selected) > limit:
        return jsonify({'success': False, 'message': f'Maximum {limit} containers allowed'}), 400

    # Validate container names exist
    all_containers = get_all_containers()
    invalid = [n for n in selected if n not in all_containers]
    if invalid:
        return jsonify({'success': False, 'message': f'Unknown containers: {", ".join(invalid)}'}), 400

    # Validate names match Docker naming convention
    import re
    for n in selected:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', n) or len(n) > 128:
            return jsonify({'success': False, 'message': f'Invalid container name: {n}'}), 400

    lm.set_managed_containers(selected)
    return jsonify({'success': True, 'message': f'{len(selected)} containers selected'})


def _is_visible_container(name):
    """Check if container is in the visible set for current tier."""
    visible = _get_visible_container_names()
    return name in visible


@bp.route('/containers/<name>/start', methods=['POST'])
@require_permission('containers.start')
def start_container(name):
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    if not _is_visible_container(name):
        return jsonify({'success': False, 'message': 'Container not in managed set'}), 403
    result = safe_docker_run(['docker', 'start', name], capture_output=True, text=True)
    if result and result.returncode == 0:
        _log_audit('CONTAINER_START', name)
        return jsonify({'success': True, 'message': f'{name} started'})
    return jsonify({'success': False, 'message': result.stderr.strip() if result else 'Docker unavailable'}), 500


@bp.route('/containers/<name>/stop', methods=['POST'])
@require_permission('containers.stop')
def stop_container(name):
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    if not _is_visible_container(name):
        return jsonify({'success': False, 'message': 'Container not in managed set'}), 403
    result = safe_docker_run(['docker', 'stop', name], capture_output=True, text=True)
    if result and result.returncode == 0:
        _log_audit('CONTAINER_STOP', name)
        return jsonify({'success': True, 'message': f'{name} stopped'})
    return jsonify({'success': False, 'message': result.stderr.strip() if result else 'Docker unavailable'}), 500


@bp.route('/containers/<name>/restart', methods=['POST'])
@require_permission('containers.restart')
def restart_container(name):
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    if not _is_visible_container(name):
        return jsonify({'success': False, 'message': 'Container not in managed set'}), 403
    result = safe_docker_run(['docker', 'restart', name], capture_output=True, text=True)
    if result and result.returncode == 0:
        return jsonify({'success': True, 'message': f'{name} restarted'})
    return jsonify({'success': False, 'message': result.stderr.strip() if result else 'Docker unavailable'}), 500


@bp.route('/containers/<name>/logs')
@require_permission('containers.logs')
def get_logs(name):
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if not _is_visible_container(name):
        return jsonify({'error': 'Container not in managed set'}), 403
    try:
        tail = min(max(int(request.args.get('tail', '100')), 1), 10000)
    except (ValueError, TypeError):
        tail = 100
    result = safe_docker_run(
        ['docker', 'logs', '--tail', str(tail), name],
        capture_output=True, text=True
    )
    if result:
        return jsonify({'logs': result.stdout, 'stderr': result.stderr})
    return jsonify({'logs': '', 'error': 'Docker unavailable'}), 500


@bp.route('/containers/<name>/inspect')
@require_permission('containers.inspect')
def inspect_container(name):
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    if not _is_visible_container(name):
        return jsonify({'error': 'Container not in managed set'}), 403
    result = safe_docker_run(['docker', 'inspect', name], capture_output=True, text=True)
    if result and result.returncode == 0:
        data = json_mod.loads(result.stdout)[0]
        state = data.get('State', {})
        config = data.get('Config', {})
        network = data.get('NetworkSettings', {})

        ports = {}
        for port, bindings in (network.get('Ports') or {}).items():
            if bindings:
                ports[port] = [{'HostPort': b.get('HostPort', ''), 'HostIp': b.get('HostIp', '')} for b in bindings]

        return jsonify({
            'name': name,
            'status': state.get('Status', 'unknown'),
            'running': state.get('Running', False),
            'started_at': state.get('StartedAt', 'N/A')[:19],
            'image': config.get('Image', 'N/A'),
            'ports': ports,
            'env': [e.split('=', 1)[0] for e in (config.get('Env') or []) if '=' in e][:20]
        })
    return jsonify({'error': 'Failed to inspect container'}), 500


@bp.route('/containers/<name>/compose')
@require_permission('containers.compose_read')
def get_compose(name):
    """Read the docker-compose YAML file for a container."""
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'error': str(e), 'content': ''}), 400
    compose_file = f"docker-compose-{name}.yml"
    if not os.path.exists(compose_file):
        return jsonify({'error': 'No compose file found', 'content': ''}), 404
    try:
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content, 'filename': compose_file})
    except Exception as e:
        return jsonify({'error': str(e), 'content': ''}), 500


@bp.route('/containers/<name>/compose', methods=['POST'])
@require_permission('containers.compose_write')
def save_compose(name):
    """Save changes to the docker-compose YAML file for a container."""
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    compose_file = f"docker-compose-{name}.yml"
    if not os.path.exists(compose_file):
        return jsonify({'success': False, 'message': 'No compose file found'}), 404

    data = request.get_json()
    content = data.get('content', '')
    if not content.strip():
        return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400

    try:
        import yaml
        yaml.safe_load(content)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Invalid YAML: {e}'}), 400

    try:
        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(content)
        _log_audit('UPDATE', name, {'action': 'compose_edit', 'source': 'web_ui'})
        return jsonify({'success': True, 'message': 'Compose file saved. Recreate the container to apply changes.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/containers/<name>/uninstall', methods=['POST'])
@require_permission('containers.uninstall')
def uninstall_container(name):
    """Completely uninstall a container, volumes, images, and files."""
    try:
        name = validate_container_name(name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    from cli.uninstall_menu import (
        _get_container_images, _volume_belongs_to_instance
    )

    removal_details = {'volumes_removed': [], 'files_removed': [], 'errors': []}
    compose_file = f"docker-compose-{name}.yml"

    # Collect images before removal
    images_to_remove = _get_container_images(name, compose_file)

    # Collect ALL volumes attached to this container (including anonymous ones)
    container_volumes = set()
    inspect_result = safe_docker_run(
        ['docker', 'inspect', '--format', '{{range .Mounts}}{{.Name}} {{end}}', name],
        capture_output=True, text=True
    )
    if inspect_result and inspect_result.returncode == 0:
        for vol in inspect_result.stdout.strip().split():
            if vol.strip():
                container_volumes.add(vol.strip())

    # 1. Stop and remove container
    safe_docker_run(['docker', 'stop', name], capture_output=True, text=True)
    result = safe_docker_run(['docker', 'rm', '-f', name], capture_output=True, text=True)
    if result and result.returncode != 0 and result.stderr and "No such container" not in result.stderr:
        removal_details['errors'].append(f"Container: {result.stderr.strip()}")

    # 2. Remove volumes: both name-matched and container-attached (anonymous)
    result = safe_docker_run(
        ['docker', 'volume', 'ls', '--format', '{{.Name}}'],
        capture_output=True, text=True
    )
    if result and result.returncode == 0:
        for vol in result.stdout.strip().split('\n'):
            if vol and (_volume_belongs_to_instance(vol, name) or vol in container_volumes):
                r = safe_docker_run(['docker', 'volume', 'rm', '-f', vol], capture_output=True, text=True)
                if r and r.returncode == 0:
                    removal_details['volumes_removed'].append(vol)

    # 3. Remove compose file, Dockerfile, config, backup files
    for path in [compose_file, f"Dockerfile-{name}"]:
        if os.path.exists(path):
            try:
                os.remove(path)
                removal_details['files_removed'].append(path)
            except Exception:
                pass

    for dir_path, pattern in [("config", f"{name}*"), ("backups", f"*{name}*")]:
        d = Path(dir_path)
        if d.exists():
            for f in d.glob(pattern):
                try:
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        shutil.rmtree(f)
                    removal_details['files_removed'].append(str(f))
                except Exception:
                    pass

    # 4. Remove instance-specific image tag
    instance_image = f"{name}:orchix"
    r = safe_docker_run(['docker', 'rmi', instance_image], capture_output=True, text=True)
    if r and r.returncode == 0:
        removal_details['files_removed'].append(f"Image: {instance_image}")

    # Remove shared images only if not used by other containers
    repos_in_use = set()
    r = safe_docker_run(['docker', 'ps', '-a', '--format', '{{.Image}}'], capture_output=True, text=True)
    if r and r.returncode == 0:
        for img in r.stdout.strip().split('\n'):
            img = img.strip()
            if img:
                repo = img.rsplit(':', 1)[0] if ':' in img else img
                repos_in_use.add(repo)

    for image in images_to_remove:
        if image == instance_image:
            continue
        img_repo = image.rsplit(':', 1)[0] if ':' in image else image
        if img_repo in repos_in_use:
            continue
        r = safe_docker_run(['docker', 'rmi', image], capture_output=True, text=True)
        if r and r.returncode == 0:
            removal_details['files_removed'].append(f"Image: {image}")

    # 5. Prune unused networks
    safe_docker_run(['docker', 'network', 'prune', '-f'], capture_output=True, text=True)

    # 6. Audit log
    _log_audit('UNINSTALL', name, removal_details)

    return jsonify({
        'success': True,
        'message': f'{name} completely uninstalled',
        'details': removal_details
    })
