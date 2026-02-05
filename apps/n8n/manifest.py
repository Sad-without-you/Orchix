# ORCHIX v1.1
from apps.n8n.installer import N8nInstaller
from apps.n8n.updater import N8nUpdater

MANIFEST = {
    # Identity
    'name': 'n8n',
    'display_name': 'n8n Workflow Automation',
    'description': 'The workflow automation platform',
    'icon': '⚡',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': N8nInstaller,
    'updater_class': N8nUpdater,
    
    # Resources
    'default_ports': [5678],
    'volumes': ['n8n_data'],
    'networks': [],
    
    # ✨ NEW: Hooks
    'hooks': {
        'backup': 'apps.n8n.hooks.backup_n8n.backup_n8n',
        'restore': 'apps.n8n.hooks.restore_n8n.restore_n8n',
        'ready_check': 'apps.n8n.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.n8n.hooks.success_message.get_success_message'
    }
}