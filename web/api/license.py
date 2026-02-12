from flask import Blueprint, jsonify, request
from web.auth import login_required

bp = Blueprint('api_license', __name__, url_prefix='/api')


@bp.route('/license')
@login_required
def get_license():
    from license import get_license_manager
    lm = get_license_manager()
    info = lm.get_license_info()

    # Serialize for JSON (handle datetime and float('inf'))
    result = {
        'tier': info['tier'],
        'tier_display': info['tier_display'],
        'is_pro': info['is_pro'],
        'days_remaining': info['days_remaining'],
        'features': {
            'max_containers': info['features']['max_containers'] if info['features']['max_containers'] != float('inf') else 999,
            'backup_restore': info['features']['backup_restore'],
            'multi_instance': info['features']['multi_instance'],
            'migration': info['features']['migration'],
            'audit_log': info['features']['audit_log'],
        },
        'container_status': {
            'current': info['container_status']['current'],
            'limit': info['container_status']['limit'] if info['container_status']['limit'] != float('inf') else 999,
            'remaining': info['container_status']['remaining'] if info['container_status']['remaining'] != float('inf') else 999,
        }
    }
    return jsonify(result)


@bp.route('/license/activate', methods=['POST'])
@login_required
def activate_license():
    data = request.json
    key = data.get('license_key')
    if not key:
        return jsonify({'success': False, 'message': 'License key required'}), 400

    from license import get_license_manager
    lm = get_license_manager()

    success = lm.activate_pro(key)
    if success:
        return jsonify({'success': True, 'message': 'PRO license activated'})
    return jsonify({'success': False, 'message': 'Invalid or expired license key'}), 400


@bp.route('/license/deactivate', methods=['POST'])
@login_required
def deactivate_license():
    from license import get_license_manager
    lm = get_license_manager()

    success = lm.deactivate()
    if success:
        return jsonify({'success': True, 'message': 'License deactivated'})
    return jsonify({'success': False, 'message': 'Failed to deactivate'}), 500
