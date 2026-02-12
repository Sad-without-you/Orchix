import os
import secrets
from datetime import timedelta
from flask import Flask, session, redirect, url_for, render_template


def create_app():
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )

    # Secret key for sessions
    secret_file = os.path.join(os.path.expanduser('~'), '.orchix_web_secret')
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            app.secret_key = f.read().strip()
    else:
        app.secret_key = secrets.token_hex(32)
        with open(secret_file, 'w') as f:
            f.write(app.secret_key)

    # Session security
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
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

    @app.route('/')
    def index():
        if not session.get('authenticated'):
            return redirect(url_for('auth.login'))
        return render_template('index.html')

    return app


def run_web(host='0.0.0.0', port=5000):
    from web.auth import ensure_password_exists
    ensure_password_exists()

    app = create_app()
    print(f"\n  ORCHIX Web UI running at http://{host}:{port}")
    print(f"  (Production server: Waitress)\n")

    from waitress import serve
    serve(app, host=host, port=port, threads=8, channel_timeout=120)
