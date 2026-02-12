import hashlib
import secrets
from pathlib import Path
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)
PASSWORD_FILE = Path.home() / '.orchix_web_password'

# Track failed login attempts: {ip: [timestamp, ...]}
_login_attempts = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes


def _hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)


def _verify_password(password):
    if not PASSWORD_FILE.exists():
        return False
    stored = PASSWORD_FILE.read_text().strip()
    # Support both old SHA256 and new pbkdf2 hashes (migration)
    if stored.startswith('pbkdf2:'):
        return check_password_hash(stored, password)
    # Legacy SHA256 fallback - auto-upgrade on successful login
    if hashlib.sha256(password.encode()).hexdigest() == stored:
        _set_password(password)  # Upgrade to pbkdf2
        return True
    return False


def _set_password(password):
    PASSWORD_FILE.write_text(_hash_password(password))


def ensure_password_exists():
    if not PASSWORD_FILE.exists():
        default_pw = secrets.token_urlsafe(12)
        _set_password(default_pw)
        print(f"  {'=' * 46}")
        print(f"  ORCHIX Web UI - First Time Setup")
        print(f"  Default password: {default_pw}")
        print(f"  Change it in Settings > Change Password")
        print(f"  {'=' * 46}")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated


def _is_rate_limited(ip):
    '''Check if IP has exceeded login attempt limit.'''
    import time
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    # Clean old attempts
    attempts = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


def _record_failed_attempt(ip):
    '''Record a failed login attempt.'''
    import time
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client_ip = request.remote_addr or '0.0.0.0'

        # Rate limiting
        if _is_rate_limited(client_ip):
            return render_template('login.html', error='Too many attempts. Please wait 5 minutes.')

        password = request.form.get('password', '')
        if _verify_password(password):
            session.clear()  # Prevent session fixation
            session['authenticated'] = True
            session.permanent = True
            # Clear failed attempts on success
            _login_attempts.pop(client_ip, None)
            return redirect('/')

        _record_failed_attempt(client_ip)
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/change-password', methods=['POST'])
def change_password():
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    current = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if not _verify_password(current):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400

    if len(new_pw) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    _set_password(new_pw)
    return jsonify({'success': True, 'message': 'Password changed'})
