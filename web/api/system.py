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


import threading

# Global lock for preventing concurrent updates
_update_lock = threading.Lock()

@bp.route('/system/update', methods=['POST'])
@login_required
def update_orchix():
    """
    Update ORCHIX to latest version via git pull + pip install.
    Returns: { success: bool, message: str, requires_restart: bool, new_version: str }
    """
    import subprocess
    import os
    import sys

    # Prevent concurrent updates
    if not _update_lock.acquire(blocking=False):
        return jsonify({
            'success': False,
            'message': 'Update already in progress'
        }), 409

    try:
        from utils.version_check import CURRENT_VERSION, check_for_updates

        # Get ORCHIX directory
        orchix_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Step 1: git pull
        result = subprocess.run(
            ['git', 'pull'],
            cwd=orchix_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )

        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': f'Git pull failed: {result.stderr[:200] if result.stderr else "Unknown error"}'
            }), 500

        # Check if already up to date
        if 'Already up to date' in result.stdout or 'Already up-to-date' in result.stdout:
            return jsonify({
                'success': True,
                'message': 'ORCHIX is already up to date',
                'requires_restart': False,
                'new_version': CURRENT_VERSION
            })

        # Step 2: pip install --upgrade
        pip_result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--upgrade'],
            cwd=orchix_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=120
        )

        if pip_result.returncode != 0:
            return jsonify({
                'success': False,
                'message': f'Update downloaded but dependency install failed: {pip_result.stderr[:200] if pip_result.stderr else "Unknown error"}'
            }), 500

        # Get new version
        new_version_result = check_for_updates()
        new_version = new_version_result.get('latest_version', CURRENT_VERSION) if new_version_result else CURRENT_VERSION

        # Audit logging (PRO only)
        try:
            from license import get_license_manager
            from license.audit_logger import get_audit_logger, AuditEventType
            lm = get_license_manager()
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.UPDATE, 'ORCHIX', {
                'old_version': CURRENT_VERSION,
                'new_version': new_version,
                'source': 'web_ui',
                'status': 'success'
            })
        except Exception:
            pass  # Don't fail update if audit logging fails

        return jsonify({
            'success': True,
            'message': f'Successfully updated to v{new_version}',
            'requires_restart': True,
            'new_version': new_version
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Update timed out. Check your internet connection.'
        }), 500
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'message': 'Git is not installed. Please install Git to use automatic updates.'
        }), 400
    except Exception as e:
        # Log failure to audit
        try:
            from license import get_license_manager
            from license.audit_logger import get_audit_logger, AuditEventType
            lm = get_license_manager()
            logger = get_audit_logger(enabled=lm.is_pro())
            logger.log_event(AuditEventType.UPDATE, 'ORCHIX', {
                'error': str(e),
                'status': 'failed',
                'source': 'web_ui'
            })
        except:
            pass

        return jsonify({
            'success': False,
            'message': f'Update failed: {str(e)}'
        }), 500
    finally:
        _update_lock.release()
