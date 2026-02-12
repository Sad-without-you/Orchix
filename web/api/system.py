from flask import Blueprint, jsonify
from web.auth import login_required

bp = Blueprint('api_system', __name__, url_prefix='/api')


@bp.route('/system')
@login_required
def get_system_info():
    from utils.system import get_platform, detect_os, detect_package_manager, check_docker, check_dependencies

    return jsonify({
        'platform': get_platform(),
        'os': detect_os(),
        'package_manager': detect_package_manager(),
        'docker': check_docker(),
        'dependencies': check_dependencies()
    })


@bp.route('/system/docker-status')
@login_required
def docker_status():
    from utils.docker_utils import check_docker_status
    return jsonify(check_docker_status())


@bp.route('/system/check-update')
@login_required
def check_update():
    from utils.version_check import check_for_updates, CURRENT_VERSION
    result = check_for_updates()
    if result is None:
        return jsonify({'current_version': CURRENT_VERSION, 'update_available': False})
    result['current_version'] = CURRENT_VERSION
    return jsonify(result)
