# ORCHIX v1.1
from apps.qdrant.installer import QdrantInstaller
from apps.qdrant.updater import QdrantUpdater


MANIFEST = {
    # Identity
    'name': 'qdrant',
    'display_name': 'Qdrant Vector Database',
    'description': 'Vector similarity search engine',
    'icon': '🔍',
    'version': '1.1.0',

    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },

    # Classes
    'installer_class': QdrantInstaller,
    'updater_class': QdrantUpdater,

    # Resources
    'default_ports': [6333, 6334],
    'volumes': ['qdrant_storage'],
    'networks': [],

    # Hooks
    'hooks': {
        'backup': 'apps.qdrant.hooks.backup_qdrant.backup_qdrant',
        'restore': 'apps.qdrant.hooks.restore_qdrant.restore_qdrant',
        'ready_check': 'apps.qdrant.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.qdrant.hooks.success_message.get_success_message'
    }
}
