# ORCHIX v1.1
from apps.lightrag.installer import LightRAGInstaller
from apps.lightrag.updater import LightRAGUpdater


MANIFEST = {
    # Identity
    'name': 'lightrag',
    'display_name': 'LightRAG - RAG framework',
    'description': 'Lightweight RAG framework',
    'icon': '💡',
    'version': '1.1.0',

    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },

    # Classes
    'installer_class': LightRAGInstaller,
    'updater_class': LightRAGUpdater,

    # Resources
    'default_ports': [8000],
    'volumes': ['lightrag_data'],
    'networks': [],

    # Hooks
    'hooks': {
        'backup': 'apps.lightrag.hooks.backup_lightrag.backup_lightrag',
        'restore': 'apps.lightrag.hooks.restore_lightrag.restore_lightrag',
        'ready_check': 'apps.lightrag.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.lightrag.hooks.success_message.get_success_message'
    }
}
