# ORCHIX v1.1
from apps.redis.installer import RedisInstaller
from apps.redis.updater import RedisUpdater


MANIFEST = {
    # Identity
    'name': 'redis',
    'display_name': 'Redis Cache Server',
    'description': 'In-memory data structure store',
    'icon': '🔴',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': RedisInstaller,
    'updater_class': RedisUpdater,
    
    # Resources
    'default_ports': [6379],
    'volumes': ['redis_data'],
    'networks': [],
    
    # ✨ NEW: Hooks
    'hooks': {
        'backup': 'apps.redis.hooks.backup_redis.backup_redis',
        'restore': 'apps.redis.hooks.restore_redis.restore_redis',
        'ready_check': 'apps.redis.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.redis.hooks.success_message.get_success_message'
    }
}