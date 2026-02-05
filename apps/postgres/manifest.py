# ORCHIX v1.1
from apps.postgres.installer import PostgresInstaller
from apps.postgres.updater import PostgresUpdater


MANIFEST = {
    # Identity
    'name': 'postgres',
    'display_name': 'PostgreSQL Database',
    'description': 'Open source relational database',
    'icon': '🐘',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': PostgresInstaller,
    'updater_class': PostgresUpdater,
    
    # Resources
    'default_ports': [5432],
    'volumes': ['postgres_data'],
    'networks': [],
    
    # ✨ NEW: Hooks
    'hooks': {
        'backup': 'apps.postgres.hooks.backup_postgres.backup_postgres',
        'restore': 'apps.postgres.hooks.restore_postgres.restore_postgres',
        'ready_check': 'apps.postgres.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.postgres.hooks.success_message.get_success_message'
    }
}