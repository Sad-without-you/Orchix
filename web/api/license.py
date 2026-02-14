from flask import Blueprint, jsonify, request
from web.auth import require_permission

bp = Blueprint('api_license', __name__, url_prefix='/api')


@bp.route('/license')
@require_permission('license.read')
def get_license():
    from license import get_license_manager
    lm = get_license_manager()
    info = lm.get_license_info()

    # Serialize for JSON (handle datetime and float('inf'))
    # max_containers is a boolean feature: true if unlimited (PRO >= 999), false if limited (FREE <= 10)
    max_containers_value = info['features']['max_containers']
    max_containers_unlimited = max_containers_value >= 999 or max_containers_value == float('inf')

    result = {
        'tier': info['tier'],
        'tier_display': info['tier_display'],
        'is_pro': info['is_pro'],
        'days_remaining': info['days_remaining'],
        'features': {
            'max_containers': max_containers_unlimited,
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
@require_permission('license.activate')
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
@require_permission('license.deactivate')
def deactivate_license():
    from license import get_license_manager
    lm = get_license_manager()

    success = lm.deactivate()
    if success:
        return jsonify({'success': True, 'message': 'License deactivated'})
    return jsonify({'success': False, 'message': 'Failed to deactivate'}), 500
