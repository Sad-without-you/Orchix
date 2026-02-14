from flask import Blueprint, jsonify, request
from web.auth import require_permission

bp = Blueprint('api_audit', __name__, url_prefix='/api')


@bp.route('/audit')
@require_permission('audit.read')
def get_audit_logs():
    from license import get_license_manager
    from license.audit_logger import get_audit_logger

    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403

    logger = get_audit_logger(enabled=True)

    event_type = request.args.get('event_type')
    app_name = request.args.get('app_name')
    try:
        limit = min(int(request.args.get('limit', '100')), 1000)
    except (ValueError, TypeError):
        limit = 100

    events = logger.get_recent_events(
        limit=limit,
        event_type=event_type,
        app_name=app_name
    )

    return jsonify(events)


@bp.route('/audit/users')
@require_permission('audit.read')
def get_audit_users():
    """Get distinct users from audit logs."""
    from license import get_license_manager
    from license.audit_logger import get_audit_logger

    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403

    logger = get_audit_logger(enabled=True)
    events = logger.get_recent_events(limit=1000)
    users = sorted(set(e.get('user', 'unknown') for e in events))
    return jsonify(users)


@bp.route('/audit/user-activity')
@require_permission('audit.read')
def get_user_activity():
    """Get audit events filtered by user."""
    from license import get_license_manager
    from license.audit_logger import get_audit_logger

    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403

    username = request.args.get('user')
    limit = int(request.args.get('limit', '50'))

    logger = get_audit_logger(enabled=True)
    events = logger.get_user_activity(username=username, limit=limit)
    return jsonify(events)


@bp.route('/audit/clear', methods=['POST'])
@require_permission('audit.clear')
def clear_audit_logs():
    """Clear old audit logs with retention period."""
    from license import get_license_manager
    from license.audit_logger import get_audit_logger

    lm = get_license_manager()
    if not lm.is_pro():
        return jsonify({'error': 'PRO license required'}), 403

    days = request.json.get('days', 90)
    if days not in [30, 90, 180, 365]:
        return jsonify({'success': False, 'message': 'Invalid retention period'}), 400

    logger = get_audit_logger(enabled=True)
    logger.clear_old_logs(days=days)
    return jsonify({'success': True, 'message': f'Cleared logs older than {days} days'})
