import json
import os
import re
import secrets
import stat
import threading
import time
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# File paths
USERS_FILE = Path.home() / '.orchix_web_users.json'
PASSWORD_FILE = Path.home() / '.orchix_web_password'  # Legacy, kept for migration

# Constants
VALID_ROLES = ('admin', 'operator', 'viewer')
FREE_MAX_USERS = 1
_MAX_PASSWORD_LENGTH = 1024

# Track failed login attempts: {ip: [timestamp, ...]}
_login_attempts = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes

# Thread lock for user data operations
_users_lock = threading.Lock()

# ============ Role Permissions ============

ROLE_PERMISSIONS = {
    'admin': {
        'dashboard.read',
        'containers.read', 'containers.start', 'containers.stop', 'containers.restart',
        'containers.logs', 'containers.inspect', 'containers.compose_read', 'containers.compose_write',
        'containers.uninstall',
        'apps.read', 'apps.install', 'apps.update',
        'backups.read', 'backups.create', 'backups.restore', 'backups.delete',
        'migration.read', 'migration.export', 'migration.import',
        'audit.read', 'audit.delete', 'audit.clear',
        'license.read', 'license.activate', 'license.deactivate',
        'system.read', 'system.update',
        'users.read', 'users.create', 'users.edit', 'users.delete',
    },
    'operator': {
        'dashboard.read',
        'containers.read', 'containers.start', 'containers.stop', 'containers.restart',
        'containers.logs', 'containers.inspect', 'containers.compose_read', 'containers.compose_write',
        'containers.uninstall',
        'apps.read', 'apps.install', 'apps.update',
        'backups.read', 'backups.create', 'backups.restore',
        'migration.read', 'migration.export', 'migration.import',
        'audit.read',
        'license.read',
        'system.read',
    },
    'viewer': {
        'dashboard.read',
        'containers.read', 'containers.logs', 'containers.inspect',
        'containers.compose_read',
        'apps.read',
        'audit.read',
        'license.read',
        'system.read',
    },
}

# ============ User Data Layer ============


def _secure_file(path):
    """Set restrictive permissions on sensitive files (600 on Linux/Mac)."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except (OSError, AttributeError):
        pass


def _load_users():
    """Load users from JSON file. Returns {'version': 1, 'users': {...}}"""
    if not USERS_FILE.exists():
        return {'version': 1, 'users': {}}
    try:
        data = json.loads(USERS_FILE.read_text(encoding='utf-8'))
        if 'version' not in data:
            # Old format: {"username": {"password_hash": "...", "role": "..."}}
            migrated = {'version': 1, 'users': {}}
            for username, info in data.items():
                migrated['users'][username] = {
                    'password_hash': info.get('password_hash', ''),
                    'role': info.get('role', 'admin'),
                    'created_at': datetime.now().isoformat(),
                    'last_login': None
                }
            _save_users(migrated)
            return migrated
        return data
    except (json.JSONDecodeError, IOError):
        return {'version': 1, 'users': {}}


def _save_users(data):
    """Save users to JSON file with atomic write and restricted permissions."""
    with _users_lock:
        tmp = USERS_FILE.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp.replace(USERS_FILE)
        _secure_file(str(USERS_FILE))


def ensure_users_exist():
    """Migrate from single-password to multi-user, or create first admin."""
    if USERS_FILE.exists():
        data = _load_users()
        if data.get('users'):
            return  # Users already exist

    # Migrate from single-password file
    if PASSWORD_FILE.exists():
        password_hash = PASSWORD_FILE.read_text().strip()
        # Ensure it's pbkdf2 format
        if not password_hash.startswith('pbkdf2:'):
            # Legacy SHA256 - we can't reverse it, generate new password
            default_pw = secrets.token_urlsafe(12)
            password_hash = generate_password_hash(default_pw, method='pbkdf2:sha256', salt_length=16)
            print(f"  {'=' * 46}")
            print(f"  ORCHIX Web UI - Migrated to Multi-User")
            print(f"  Username: admin")
            print(f"  New Password: {default_pw}")
            print(f"  (Legacy password format could not be migrated)")
            print(f"  {'=' * 46}")
        else:
            print(f"  Migrated single password to admin user")

        users_data = {
            'version': 1,
            'users': {
                'admin': {
                    'password_hash': password_hash,
                    'role': 'admin',
                    'created_at': datetime.now().isoformat(),
                    'last_login': None
                }
            }
        }
        _save_users(users_data)
        return

    # Fresh install
    default_pw = secrets.token_urlsafe(12)
    users_data = {
        'version': 1,
        'users': {
            'admin': {
                'password_hash': generate_password_hash(default_pw, method='pbkdf2:sha256', salt_length=16),
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
        }
    }
    _save_users(users_data)
    print(f"  {'=' * 46}")
    print(f"  ORCHIX Web UI - First Time Setup")
    print(f"  Username: admin")
    print(f"  Password: {default_pw}")
    print(f"  Change it in Settings > User Management")
    print(f"  {'=' * 46}")


# ============ Decorators ============

def login_required(f):
    """Check if user is authenticated. Kept for backward compatibility."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated


def require_permission(*permissions):
    """Check if user has at least one of the specified permissions."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            user_role = session.get('role', 'viewer')
            user_perms = ROLE_PERMISSIONS.get(user_role, set())
            if not any(p in user_perms for p in permissions):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============ Rate Limiting ============

def _is_rate_limited(ip):
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


def _record_failed_attempt(ip):
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())


def _cleanup_rate_limits():
    """Remove expired entries to prevent memory leak."""
    now = time.time()
    expired = [ip for ip, attempts in _login_attempts.items()
               if all(now - t >= _LOCKOUT_SECONDS for t in attempts)]
    for ip in expired:
        del _login_attempts[ip]


# ============ Routes ============

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client_ip = request.remote_addr or '0.0.0.0'

        if _is_rate_limited(client_ip):
            return render_template('login.html', error='Too many attempts. Please wait 5 minutes.')

        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')

        # Limit password length to prevent DoS via expensive hashing
        if len(password) > _MAX_PASSWORD_LENGTH:
            _record_failed_attempt(client_ip)
            return render_template('login.html', error='Invalid username or password')

        users_data = _load_users()
        user = users_data.get('users', {}).get(username)

        if user and check_password_hash(user['password_hash'], password):
            # Enforce user limit: on FREE tier, only admin users can log in
            try:
                from license import get_license_manager
                lm = get_license_manager()
                if not lm.is_pro() and user.get('role') != 'admin':
                    return render_template('login.html',
                        error='User limit reached (FREE tier). Only admin can log in. Upgrade to PRO for multi-user.')
            except Exception:
                pass

            session.clear()
            session['authenticated'] = True
            session['username'] = username
            session['role'] = user.get('role', 'viewer')
            session.permanent = True

            # Update last_login
            users_data['users'][username]['last_login'] = datetime.now().isoformat()
            _save_users(users_data)

            _login_attempts.pop(client_ip, None)
            _cleanup_rate_limits()
            return redirect('/')

        _record_failed_attempt(client_ip)
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/me')
@login_required
def get_current_user():
    """Return current user info."""
    username = session.get('username', 'unknown')
    role = session.get('role', 'viewer')
    permissions = sorted(ROLE_PERMISSIONS.get(role, set()))
    return jsonify({
        'username': username,
        'role': role,
        'permissions': permissions
    })


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    current = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    username = session.get('username')

    if not username:
        return jsonify({'success': False, 'message': 'No user session'}), 401

    if len(new_pw) > _MAX_PASSWORD_LENGTH:
        return jsonify({'success': False, 'message': 'Password too long'}), 400

    users_data = _load_users()
    user = users_data.get('users', {}).get(username)

    if not user or not check_password_hash(user['password_hash'], current):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

    if len(new_pw) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

    users_data['users'][username]['password_hash'] = generate_password_hash(
        new_pw, method='pbkdf2:sha256', salt_length=16
    )
    _save_users(users_data)
    return jsonify({'success': True, 'message': 'Password changed'})
