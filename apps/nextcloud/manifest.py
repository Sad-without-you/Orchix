# ORCHIX v1.1
from apps.nextcloud.installer import NextcloudInstaller
from apps.nextcloud.updater import NextcloudUpdater

MANIFEST = {
    # Identity
    'name': 'nextcloud',
    'display_name': 'Nextcloud Cloud Storage',
    'description': 'Self-hosted cloud storage solution',
    'icon': '☁️',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': NextcloudInstaller,
    'updater_class': NextcloudUpdater,
    
    # Resources
    'default_ports': [8085],
    'volumes': ['nextcloud_data'],
    'networks': [],
    
    # ✨ Hooks
    'hooks': {
        'backup': 'apps.nextcloud.hooks.backup_nextcloud.backup_nextcloud',
        'restore': 'apps.nextcloud.hooks.restore_nextcloud.restore_nextcloud',
        'ready_check': 'apps.nextcloud.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.nextcloud.hooks.success_message.get_success_message'
    }
}