# ORCHIX v1.1
from apps.vaultwarden.installer import VaultwardenInstaller
from apps.vaultwarden.updater import update_vaultwarden

MANIFEST = {
    # Identity
    'name': 'vaultwarden',
    'display_name': 'Vaultwarden Password Manager',
    'description': 'Lightweight Bitwarden-compatible password manager',
    'icon': '🔐',
    'version': '1.30.5',

    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },

    # Classes
    'installer_class': VaultwardenInstaller,
    'updater_class': update_vaultwarden,

    # Resources
    'default_ports': [8080],
    'volumes': ['vaultwarden_data'],
    'networks': [],

    # Hooks
    'hooks': {
        'success_message': 'apps.vaultwarden.hooks.success_message.get_success_message'
    }
}
