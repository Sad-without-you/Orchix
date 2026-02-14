import re
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash
from web.auth import require_permission, _load_users, _save_users, VALID_ROLES, FREE_MAX_USERS, _MAX_PASSWORD_LENGTH

bp = Blueprint('api_users', __name__, url_prefix='/api')

_USERNAME_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{2,31}$')


@bp.route('/users', methods=['GET'])
@require_permission('users.read')
def list_users():
    users_data = _load_users()
    result = []
    for username, info in users_data.get('users', {}).items():
        result.append({
            'username': username,
            'role': info.get('role', 'viewer'),
            'created_at': info.get('created_at'),
            'last_login': info.get('last_login'),
        })
    return jsonify({'success': True, 'users': result})


@bp.route('/users', methods=['POST'])
@require_permission('users.create')
def create_user():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'viewer')

    if not _USERNAME_RE.match(username):
        return jsonify({'success': False, 'message': 'Username: 3-32 chars, lowercase alphanumeric/underscore/hyphen'}), 400
    if len(password) < 8 or len(password) > _MAX_PASSWORD_LENGTH:
        return jsonify({'success': False, 'message': 'Password must be 8-1024 characters'}), 400
    if role not in VALID_ROLES:
        return jsonify({'success': False, 'message': f'Role must be one of: {", ".join(VALID_ROLES)}'}), 400

    users_data = _load_users()

    # Check user limit based on license tier
    try:
        from license import get_license_manager
        lm = get_license_manager()
        max_users = lm.get_feature('max_users') or FREE_MAX_USERS
        current_users = len(users_data.get('users', {}))
        if current_users >= max_users:
            tier = lm.get_tier_display()
            return jsonify({'success': False, 'message': f'{tier} tier: max {max_users} users reached.'}), 403
    except Exception:
        pass

    if username in users_data.get('users', {}):
        return jsonify({'success': False, 'message': 'Username already exists'}), 409

    users_data['users'][username] = {
        'password_hash': generate_password_hash(password, method='pbkdf2:sha256', salt_length=16),
        'role': role,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    _save_users(users_data)

    return jsonify({'success': True, 'message': f'User {username} created'})


@bp.route('/users/<username>', methods=['PUT'])
@require_permission('users.edit')
def edit_user(username):
    data = request.json or {}
    users_data = _load_users()

    if username not in users_data.get('users', {}):
        return jsonify({'success': False, 'message': 'User not found'}), 404

    new_role = data.get('role')
    new_password = data.get('password')

    if new_role:
        if new_role not in VALID_ROLES:
            return jsonify({'success': False, 'message': f'Role must be one of: {", ".join(VALID_ROLES)}'}), 400

        # Prevent demoting the last admin
        if users_data['users'][username].get('role') == 'admin' and new_role != 'admin':
            admin_count = sum(1 for u in users_data['users'].values() if u.get('role') == 'admin')
            if admin_count <= 1:
                return jsonify({'success': False, 'message': 'Cannot demote the last admin'}), 400

        users_data['users'][username]['role'] = new_role

    if new_password:
        if len(new_password) < 8 or len(new_password) > _MAX_PASSWORD_LENGTH:
            return jsonify({'success': False, 'message': 'Password must be 8-1024 characters'}), 400
        users_data['users'][username]['password_hash'] = generate_password_hash(
            new_password, method='pbkdf2:sha256', salt_length=16
        )

    _save_users(users_data)
    return jsonify({'success': True, 'message': f'User {username} updated'})


@bp.route('/users/<username>', methods=['DELETE'])
@require_permission('users.delete')
def delete_user(username):
    current_user = session.get('username')

    if username == current_user:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400

    users_data = _load_users()

    if username not in users_data.get('users', {}):
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Prevent deleting the last admin
    if users_data['users'][username].get('role') == 'admin':
        admin_count = sum(1 for u in users_data['users'].values() if u.get('role') == 'admin')
        if admin_count <= 1:
            return jsonify({'success': False, 'message': 'Cannot delete the last admin'}), 400

    del users_data['users'][username]
    _save_users(users_data)
    return jsonify({'success': True, 'message': f'User {username} deleted'})
