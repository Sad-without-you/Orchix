from flask import Blueprint, jsonify, request
from web.auth import require_permission
from utils.validation import validate_container_name, validate_port

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
        })
    return jsonify({'fields': fields, 'is_template': True})


@bp.route('/apps/install', methods=['POST'])
@require_permission('apps.install')
def install_app():
    data = request.json
    app_name = data.get('app_name')
    instance_name = data.get('instance_name', app_name)
    user_config = data.get('config', {})

    if not app_name:
        return jsonify({'success': False, 'message': 'app_name required'}), 400

    # Check Docker status first
    from utils.docker_utils import check_docker_status
    docker = check_docker_status()
    if not docker.get('running'):
        return jsonify({'success': False, 'message': docker.get('message', 'Docker is not running')}), 503

    # Validate names to prevent path traversal and injection
    try:
        app_name = validate_container_name(app_name)
        instance_name = validate_container_name(instance_name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # Validate port
    try:
        raw_port = user_config.get('port')
        if raw_port is not None:
            user_config['port'] = validate_port(raw_port)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    from apps.manifest_loader import load_manifest
    from utils.license_check import can_install_app
    from license import get_license_manager

    try:
        manifest = load_manifest(app_name)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # License check
    check = can_install_app(manifest)
    if not check['allowed']:
        return jsonify({'success': False, 'message': 'PRO license required'}), 403

    # Container limit check - count only managed/visible containers
    lm = get_license_manager()
    if lm.is_free():
        from cli.container_menu import get_visible_containers
        visible, _ = get_visible_containers()
        limit = lm.get_container_limit()
        if len(visible) >= limit:
            return jsonify({'success': False, 'message': f"Container limit reached ({limit})"}), 403

    # Multi-instance protection: FREE tier ALWAYS uses app_name as instance_name
    from cli.install_menu import check_container_exists
    if lm.is_free():
        # Force instance_name to app_name - no custom names for FREE tier
        instance_name = app_name
        if check_container_exists(app_name):
            return jsonify({
                'success': False,
                'message': f"Container '{app_name}' already exists. Multi-Instance requires PRO."
            }), 403

    # Get installer
    InstallerClass = manifest.get('installer_class')
    if not InstallerClass:
        return jsonify({'success': False, 'message': 'No installer available'}), 400

    installer = InstallerClass(manifest)

    # Build config
    default_port = manifest.get('default_ports', [5678])
    config = {
        'port': user_config.get('port', default_port[0] if default_port else 5678),
        'instance_name': instance_name,
        'volume_name': f"{instance_name}_data",
    }

    # For template apps: process env vars via get_web_configuration
    if manifest.get('_is_template') and hasattr(installer, 'get_web_configuration'):
        env_config = installer.get_web_configuration(user_config)
        config.update(env_config)

    config.update(user_config)

    try:
        success = installer.install(config, instance_name)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Installation error: {str(e)}'}), 500

    if success:
        # Audit log
        try:
            from license.audit_logger import get_audit_logger, AuditEventType
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.INSTALL, app_name, {
                'instance_name': instance_name,
                'port': config.get('port'),
                'source': 'web_ui'
            })
        except Exception:
            pass

        # Build access info
        access_info = _get_access_info(manifest, config, instance_name)
        return jsonify({
            'success': True,
            'message': f'{instance_name} installed successfully',
            'access_info': access_info
        })

    # Check if Docker stopped during install
    docker_after = check_docker_status()
    if not docker_after.get('running'):
        return jsonify({'success': False, 'message': docker_after.get('message', 'Docker stopped during installation')}), 503

    return jsonify({'success': False, 'message': 'Installation failed. Check container logs for details.'}), 500


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

    # Post-install hints (OS-aware setup commands)
    hint_key = template.get('post_install_hint', '')
    if hint_key:
        from utils.system import is_windows
        hint = _POST_INSTALL_HINTS.get(hint_key)
        if hint:
            platform = 'windows' if is_windows() else 'linux'
            cmd = hint[platform].replace('{name}', instance_name)
            info['setup_hint'] = {'title': hint['title'], 'command': cmd}

    return info


_POST_INSTALL_HINTS = {
    'pihole_password': {
        'title': 'Set Admin Password:',
        'windows': 'docker exec -it {name} pihole -a -p YOUR_PASSWORD',
        'linux': 'sudo docker exec -it {name} pihole -a -p YOUR_PASSWORD',
    },
}


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
