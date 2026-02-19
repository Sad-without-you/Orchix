from flask import Blueprint, jsonify, request, Response, stream_with_context
from web.auth import require_permission
from utils.validation import validate_container_name, validate_port
import json

bp = Blueprint('api_apps', __name__, url_prefix='/api')


@bp.route('/apps')
@require_permission('apps.read')
def list_apps():
    from apps.manifest_loader import load_all_manifests
    from utils.license_check import can_install_app, get_app_badge

    manifests = load_all_manifests()
    apps = []
    for app_name, manifest in manifests.items():
        license_check = can_install_app(manifest)
        apps.append({
            'name': app_name,
            'display_name': manifest.get('display_name', app_name),
            'description': manifest.get('description', ''),
            'icon': manifest.get('icon', ''),
            'version': manifest.get('version', ''),
            'default_ports': manifest.get('default_ports', []),
            'license_required': manifest.get('license_required'),
            'can_install': license_check['allowed'],
            'badge': get_app_badge(manifest),
            'image_size_mb': manifest.get('image_size_mb', 0),
        })
    return jsonify(apps)


@bp.route('/apps/<name>/config-schema')
@require_permission('apps.read')
def get_config_schema(name):
    """Return config fields for template apps (used by Web UI for dynamic forms)."""
    from apps.manifest_loader import load_manifest

    try:
        manifest = load_manifest(name)
    except ValueError:
        return jsonify({'fields': [], 'is_template': False})

    if not manifest.get('_is_template'):
        return jsonify({'fields': [], 'is_template': False})

    template = manifest.get('_template', {})
    fields = []
    for env in template.get('env', []):
        fields.append({
            'key': env['key'],
            'label': env.get('label', env['key']),
            'type': env.get('type', 'text'),
            'default': env.get('default', ''),
            'required': env.get('required', False),
            'generate': env.get('generate', False),
            'options': env.get('options', []),
            'role': env.get('role', ''),
            'db_credential': env.get('db_credential', ''),
            'db_types': env.get('db_types', []),
            'db_port': env.get('db_port', False),
        })
    return jsonify({'fields': fields, 'is_template': True})


@bp.route('/apps/db-candidates')
@require_permission('apps.read')
def get_db_candidates():
    """Return running ORCHIX containers that look like database servers."""
    from utils.db_discovery import discover_db_containers
    db_types_param = request.args.get('db_types', '')
    db_types = [t.strip() for t in db_types_param.split(',') if t.strip()] or None
    return jsonify(discover_db_containers(db_types=db_types))


@bp.route('/apps/db-credentials/<container_name>')
@require_permission('apps.read')
def get_db_credentials_endpoint(container_name):
    """Return user/password/database credentials for a DB container."""
    try:
        container_name = validate_container_name(container_name)
    except ValueError:
        return jsonify({}), 400
    from utils.db_discovery import get_db_credentials
    return jsonify(get_db_credentials(container_name))


@bp.route('/apps/install-stream', methods=['POST'])
@require_permission('apps.install')
def install_stream():
    """Install app with Server-Sent Events progress streaming."""
    import subprocess
    import re
    from utils.docker_utils import safe_docker_run

    data = request.json
    app_name = data.get('app_name')
    instance_name = data.get('instance_name', app_name)
    user_config = data.get('config', {})

    def generate():
        try:
            # Validation & setup (same as normal install)
            from apps.manifest_loader import load_all_manifests
            from license.manager import get_license_manager

            manifests = load_all_manifests()
            manifest = manifests.get(app_name)
            if not manifest:
                yield f"data: {json.dumps({'error': 'App not found'})}\n\n"
                return

            lm = get_license_manager()
            limit = lm.get_container_limit()

            from cli.container_menu import get_all_containers
            current = len(get_all_containers())
            if current >= limit:
                yield f"data: {json.dumps({'error': f'Container limit reached ({limit})'})}\n\n"
                return

            from cli.install_menu import check_container_exists
            if lm.is_free():
                instance_name_final = app_name
                if check_container_exists(app_name):
                    yield f"data: {json.dumps({'error': 'Container already exists. Multi-Instance requires PRO.'})}\n\n"
                    return
            else:
                instance_name_final = instance_name

            InstallerClass = manifest.get('installer_class')
            if not InstallerClass:
                yield f"data: {json.dumps({'error': 'No installer available'})}\n\n"
                return

            installer = InstallerClass(manifest)

            # Build config
            default_port = manifest.get('default_ports', [5678])
            config = {
                'port': user_config.get('port', default_port[0] if default_port else 5678),
                'instance_name': instance_name_final,
                'volume_name': f"{instance_name_final}_data",
            }

            if manifest.get('_is_template') and hasattr(installer, 'get_web_configuration'):
                env_config = installer.get_web_configuration(user_config)
                config.update(env_config)

            config.update(user_config)

            # Get image name for pull tracking
            template = manifest.get('_template', {})
            image = template.get('image', '')

            # Stream progress: Pull image with progress tracking
            if image:
                yield f"data: {json.dumps({'progress': 10, 'status': 'Pulling image...'})}\n\n"

                # Pull image with progress
                process = subprocess.Popen(
                    ['docker', 'pull', image],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                layers_total = 0
                layers_done = 0
                last_progress = 10

                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break

                    # Count total layers
                    if 'Pulling fs layer' in line:
                        layers_total += 1
                    elif 'Pull complete' in line or 'Already exists' in line:
                        layers_done += 1

                    # Calculate progress based on completed layers
                    if layers_total > 0:
                        layer_pct = int((layers_done / layers_total) * 100)
                        progress = 10 + int(layer_pct * 0.6)  # Scale 0-100% to 10-70%
                        if progress > last_progress:
                            last_progress = progress
                            status = f"Pulling image... ({layers_done}/{layers_total} layers)"
                            yield f"data: {json.dumps({'progress': progress, 'status': status})}\n\n"

                process.wait()
                yield f"data: {json.dumps({'progress': 70, 'status': 'Image pulled'})}\n\n"

            # Install (compose up)
            yield f"data: {json.dumps({'progress': 75, 'status': 'Starting container...'})}\n\n"

            success = installer.install(config, instance_name_final)

            if success:
                yield f"data: {json.dumps({'progress': 95, 'status': 'Finalizing...'})}\n\n"

                # Audit log
                try:
                    from license.audit_logger import get_audit_logger, AuditEventType
                    logger = get_audit_logger(enabled=lm.is_pro())
                    logger.log_event(AuditEventType.INSTALL, app_name, {
                        'instance_name': instance_name_final,
                        'port': config.get('port'),
                        'source': 'web_ui'
                    })
                except Exception:
                    pass

                # Build access info
                access_info = _get_access_info(manifest, config, instance_name_final)
                response = {
                    'success': True,
                    'message': f'{instance_name_final} installed successfully',
                    'access_info': access_info,
                    'progress': 100
                }

                # Include post-install action if available
                action = template.get('post_install_action')
                if action and action.get('type') == 'set_password':
                    response['post_install_action'] = {
                        'type': 'set_password',
                        'prompt': action['prompt'],
                        'container_name': instance_name_final,
                    }

                yield f"data: {json.dumps(response)}\n\n"
            else:
                err = installer.get_last_error() if hasattr(installer, 'get_last_error') else ''
                yield f"data: {json.dumps({'error': f'Installation failed: {err}'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@bp.route('/apps/update', methods=['POST'])
@require_permission('apps.update')
def update_app():
    """Update a container application."""
    data = request.json
    container_name = data.get('container_name')
    update_type = data.get('update_type', 'version_update')

    if not container_name:
        return jsonify({'success': False, 'message': 'container_name required'}), 400

    try:
        container_name = validate_container_name(container_name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # Whitelist update types
    allowed_update_types = {'version_update', 'config_update', 'beta_update', 'next_update'}
    if update_type not in allowed_update_types:
        return jsonify({'success': False, 'message': 'Invalid update type'}), 400

    from apps.manifest_loader import load_all_manifests
    from cli.update_menu import _resolve_manifest, _retag_after_update
    from license import get_license_manager

    manifests = load_all_manifests()
    manifest = _resolve_manifest(container_name, manifests)

    if not manifest:
        return jsonify({'success': False, 'message': f'No manifest found for {container_name}'}), 400

    UpdaterClass = manifest.get('updater_class')
    if not UpdaterClass:
        return jsonify({'success': False, 'message': 'No updater available'}), 400

    updater = UpdaterClass(manifest)
    actions = updater.get_available_actions()
    if update_type not in actions:
        return jsonify({'success': False, 'message': f'Update type "{update_type}" not available'}), 400

    try:
        method = getattr(updater, update_type, None)
        if not method:
            return jsonify({'success': False, 'message': f'Unknown update type: {update_type}'}), 400
        success = method()
    except Exception as e:
        return jsonify({'success': False, 'message': f'Update error: {str(e)}'}), 500

    if success:
        _retag_after_update(container_name)
        try:
            from license.audit_logger import get_audit_logger, AuditEventType
            lm = get_license_manager()
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.UPDATE, container_name, {
                'update_type': update_type, 'status': 'success', 'source': 'web_ui'
            })
        except Exception:
            pass
        return jsonify({'success': True, 'message': f'{container_name} updated successfully'})

    return jsonify({'success': False, 'message': 'Update failed'}), 500


@bp.route('/apps/update-stream', methods=['POST'])
@require_permission('apps.update')
def update_app_stream():
    """Update app with Server-Sent Events progress streaming."""
    import subprocess
    import re

    data = request.json
    container_name = data.get('container_name')
    update_type = data.get('update_type', 'version_update')

    def generate():
        try:
            if not container_name:
                yield f"data: {json.dumps({'error': 'container_name required'})}\n\n"
                return

            try:
                validated_name = validate_container_name(container_name)
            except ValueError as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                return

            allowed_update_types = {'version_update', 'config_update', 'beta_update', 'next_update'}
            if update_type not in allowed_update_types:
                yield f"data: {json.dumps({'error': 'Invalid update type'})}\n\n"
                return

            from apps.manifest_loader import load_all_manifests
            from cli.update_menu import _resolve_manifest, _retag_after_update
            from license import get_license_manager

            manifests = load_all_manifests()
            manifest = _resolve_manifest(validated_name, manifests)

            if not manifest:
                yield f"data: {json.dumps({'error': f'No manifest found for {validated_name}'})}\n\n"
                return

            UpdaterClass = manifest.get('updater_class')
            if not UpdaterClass:
                yield f"data: {json.dumps({'error': 'No updater available'})}\n\n"
                return

            updater = UpdaterClass(manifest)
            actions = updater.get_available_actions()
            if update_type not in actions:
                yield f"data: {json.dumps({'error': f'Update type \"{update_type}\" not available'})}\n\n"
                return

            yield f"data: {json.dumps({'progress': 10, 'status': 'Pulling latest image...'})}\n\n"

            # Get image from manifest for pull tracking
            template = manifest.get('_template', {})
            image = template.get('image', '')

            if image:
                # Pull new image with progress
                process = subprocess.Popen(
                    ['docker', 'pull', image],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                layers_total = 0
                layers_done = 0
                last_progress = 10

                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break

                    if 'Pulling fs layer' in line:
                        layers_total += 1
                    elif 'Pull complete' in line or 'Already exists' in line:
                        layers_done += 1

                    if layers_total > 0:
                        pct = int((layers_done / layers_total) * 100)
                        progress = 10 + int(pct * 0.6)  # 10-70%
                        if progress > last_progress:
                            last_progress = progress
                            status = f"Pulling image... ({layers_done}/{layers_total} layers)"
                            yield f"data: {json.dumps({'progress': progress, 'status': status})}\n\n"

                process.wait()
                if process.returncode != 0:
                    yield f"data: {json.dumps({'error': 'Failed to pull new image'})}\n\n"
                    return

            yield f"data: {json.dumps({'progress': 75, 'status': 'Updating container...'})}\n\n"

            # Run update
            method = getattr(updater, update_type, None)
            if not method:
                yield f"data: {json.dumps({'error': f'Unknown update type: {update_type}'})}\n\n"
                return

            success = method()

            if success:
                _retag_after_update(validated_name)
                yield f"data: {json.dumps({'progress': 95, 'status': 'Finalizing...'})}\n\n"

                # Audit log
                try:
                    from license.audit_logger import get_audit_logger, AuditEventType
                    lm = get_license_manager()
                    logger = get_audit_logger(enabled=lm.is_pro())
                    logger.log_event(AuditEventType.UPDATE, validated_name, {
                        'update_type': update_type, 'status': 'success', 'source': 'web_ui'
                    })
                except Exception:
                    pass

                yield f"data: {json.dumps({'success': True, 'message': f'{validated_name} updated successfully', 'progress': 100})}\n\n"
            else:
                yield f"data: {json.dumps({'error': 'Update failed'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@bp.route('/apps/set-password', methods=['POST'])
@require_permission('apps.install')
def set_container_password():
    """Set password for a container after installation (e.g. Pi-hole)."""
    from utils.docker_utils import safe_docker_run

    data = request.json
    container_name = data.get('container_name', '')
    password = data.get('password', '')

    if not container_name or not password:
        return jsonify({'success': False, 'message': 'container_name and password required'}), 400

    try:
        container_name = validate_container_name(container_name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # Find the manifest to get the command template
    from apps.manifest_loader import load_all_manifests
    from cli.update_menu import _resolve_manifest

    manifests = load_all_manifests()
    manifest = _resolve_manifest(container_name, manifests)
    if not manifest:
        return jsonify({'success': False, 'message': 'Unknown container'}), 400

    template = manifest.get('_template', {})
    action = template.get('post_install_action')
    if not action or action.get('type') != 'set_password':
        return jsonify({'success': False, 'message': 'No password action for this app'}), 400

    cmd = action['command'].replace('{name}', container_name).replace('{password}', password)
    result = safe_docker_run(cmd.split(), capture_output=True, text=True)

    if result and result.returncode == 0:
        return jsonify({'success': True, 'message': 'Password set successfully'})
    return jsonify({'success': False, 'message': 'Failed to set password'}), 500


@bp.route('/apps/check-conflicts')
@require_permission('apps.read')
def check_conflicts():
    """Check if container name or port is already in use."""
    from cli.install_menu import check_container_exists, is_port_in_use

    name = request.args.get('name', '').strip()
    port = request.args.get('port', '').strip()

    result = {}
    if name:
        result['name_conflict'] = check_container_exists(name)
    if port:
        try:
            result['port_conflict'] = is_port_in_use(int(port))
        except ValueError:
            result['port_conflict'] = False
    return jsonify(result)


@bp.route('/apps/update-actions/<container_name>')
@require_permission('apps.read')
def get_update_actions(container_name):
    """Get available update actions for a container."""
    from apps.manifest_loader import load_all_manifests
    from cli.update_menu import _resolve_manifest

    manifests = load_all_manifests()
    manifest = _resolve_manifest(container_name, manifests)

    if not manifest:
        return jsonify({'actions': []})

    UpdaterClass = manifest.get('updater_class')
    if not UpdaterClass:
        return jsonify({'actions': []})

    updater = UpdaterClass(manifest)
    actions = updater.get_available_actions()
    labels = {
        'version_update': 'Update to Latest (Stable)',
        'config_update': 'Configuration Update',
        'beta_update': 'Update to Beta',
        'next_update': 'Update to Next',
    }
    return jsonify({'actions': [{'key': a, 'label': labels.get(a, a)} for a in actions]})


def _get_access_info(manifest, config, instance_name):
    """Auto-detect access info from template data. No hardcoding needed."""
    port = config.get('port', '')
    template = manifest.get('_template', {})
    ports = template.get('ports', [])
    envs = template.get('env', [])
    image = template.get('image', manifest.get('image', ''))

    # Detect access type from port labels
    web_keywords = {'web ui', 'http', 'https', 'dashboard', 'admin', 'console'}
    has_web = any(
        any(kw in p.get('label', '').lower() for kw in web_keywords)
        for p in ports
    )

    info = {'credentials': []}

    if not ports:
        info['type'] = 'none'
        info['note'] = 'Runs in background (no access needed)'
    elif has_web:
        info['type'] = 'web'
        info['url'] = f'http://localhost:{port}'
    else:
        info['type'] = 'cli'
        info['host'] = f'localhost:{port}'
        cli_cmd = _detect_cli_command(image, config, instance_name)
        if cli_cmd:
            info['command'] = cli_cmd

    # Auto-detect credentials from env vars with type=password or generate=true
    for env in envs:
        val = config.get(env['key'])
        if val and (env.get('type') == 'password' or env.get('generate')):
            info['credentials'].append({'label': env.get('label', env['key']), 'value': val})
        elif val and env.get('key', '').upper().endswith(('_USER', '_USERNAME')):
            info['credentials'].append({'label': env.get('label', env['key']), 'value': val})

    # Default credentials (built into the image, not from env vars)
    for dc in template.get('default_credentials', []):
        info['credentials'].append({'label': dc['label'], 'value': dc['value']})

    # Credentials from container logs (e.g. filebrowser generates random password)
    if template.get('credentials_from_logs'):
        log_creds = _extract_credentials_from_logs(instance_name)
        if log_creds:
            info['credentials'].extend(log_creds)

    return info


def _extract_credentials_from_logs(instance_name):
    """Extract auto-generated credentials from container logs."""
    import re
    from utils.docker_utils import safe_docker_run

    result = safe_docker_run(
        ['docker', 'logs', '--tail', '50', instance_name],
        capture_output=True, text=True
    )
    if not result or result.returncode != 0:
        return []

    logs = (result.stdout or '') + (result.stderr or '')
    creds = []

    # Pattern: "User 'X' initialized with randomly generated password: Y"
    m = re.search(
        r"[Uu]ser\s+'?(\w+)'?\s+initialized\s+with.*password:\s*(\S+)", logs
    )
    if m:
        creds.append({'label': 'Username', 'value': m.group(1)})
        creds.append({'label': 'Password', 'value': m.group(2)})
        return creds

    # Generic pattern: "password: XYZ" or "Password: XYZ"
    m = re.search(r'[Pp]assword:\s*(\S{8,})', logs)
    if m:
        creds.append({'label': 'Generated Password', 'value': m.group(1)})

    return creds


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
