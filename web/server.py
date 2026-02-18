import os
import secrets
import stat
from datetime import timedelta
from flask import Flask, session, redirect, url_for, render_template


def _secure_file(path):
    """Set restrictive permissions on sensitive files (600 on Linux/Mac)."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except (OSError, AttributeError):
        pass  # Windows handles permissions differently


def create_app():
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )

    # Secret key for sessions
    from config import ORCHIX_CONFIG_DIR
    secret_file = ORCHIX_CONFIG_DIR / '.orchix_web_secret'
    if secret_file.exists():
        with open(secret_file, 'r') as f:
            app.secret_key = f.read().strip()
    else:
        app.secret_key = secrets.token_hex(32)
        with open(secret_file, 'w') as f:
            f.write(app.secret_key)
        _secure_file(secret_file)

    # Session security
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ORCHIX_HTTPS', '').lower() == 'true'

    # Request size limit (16 MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # CSRF protection
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        if os.environ.get('ORCHIX_HTTPS', '').lower() == 'true':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Register auth blueprint
    from web.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register API blueprints
    from web.api.dashboard import bp as dashboard_bp
    from web.api.containers import bp as containers_bp
    from web.api.apps import bp as apps_bp
    from web.api.backups import bp as backups_bp
    from web.api.audit import bp as audit_bp
    from web.api.license import bp as license_bp
    from web.api.system import bp as system_bp
    from web.api.migration import bp as migration_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(containers_bp)
    app.register_blueprint(apps_bp)
    app.register_blueprint(backups_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(license_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(migration_bp)

    from web.api.users import bp as users_bp
    app.register_blueprint(users_bp)

    @app.route('/')
    def index():
        if not session.get('authenticated'):
            return redirect(url_for('auth.login'))
        return render_template('index.html')

    return app


def run_web(host='0.0.0.0', port=5000):
    from web.auth import ensure_users_exist
    ensure_users_exist()

    app = create_app()
    print(f"\n  ORCHIX Web UI running at http://{host}:{port}")
    print(f"  (Production server: Waitress)\n")

    from waitress import serve
    serve(app, host=host, port=port, threads=8, channel_timeout=120)
