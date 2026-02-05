# ORCHIX v1.1
from apps.nginx.installer import NginxInstaller
from apps.nginx.updater import NginxUpdater

MANIFEST = {
    # Identity
    'name': 'nginx',
    'display_name': 'Nginx Proxy Manager',
    'description': 'Easy SSL reverse proxy with Let\'s Encrypt',
    'icon': '🔒',
    'version': '1.1.0',
    
    # LICENSE REQUIREMENT
    'license_required': None,
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': NginxInstaller,
    'updater_class': NginxUpdater,
    
    # Resources
    'default_ports': [8080, 8081, 8443],
    'volumes': ['nginx_data', 'nginx_letsencrypt'],
    'networks': [],
    
    # Hooks
    'hooks': {
        'backup': 'apps.nginx.hooks.backup_nginx.backup_nginx',
        'restore': 'apps.nginx.hooks.restore_nginx.restore_nginx',
        'ready_check': 'apps.nginx.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.nginx.hooks.success_message.get_success_message'
    }
}