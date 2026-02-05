# ORCHIX v1.1
from apps.jellyfin.installer import JellyfinInstaller
from apps.jellyfin.updater import JellyfinUpdater

MANIFEST = {
    # Identity
    'name': 'jellyfin',
    'display_name': 'Jellyfin Media Server',
    'description': 'Free Software Media Server',
    'icon': '🎬',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': JellyfinInstaller,
    'updater_class': JellyfinUpdater,
    
    # Resources
    'default_ports': [8096, 8920],
    'volumes': ['jellyfin_config', 'jellyfin_cache'],
    'networks': [],
    
    # ✨ Hooks
    'hooks': {
        'backup': 'apps.jellyfin.hooks.backup_jellyfin.backup_jellyfin',
        'restore': 'apps.jellyfin.hooks.restore_jellyfin.restore_jellyfin',
        'ready_check': 'apps.jellyfin.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.jellyfin.hooks.success_message.get_success_message'
    }
}