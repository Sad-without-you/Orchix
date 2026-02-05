# ORCHIX v1.1
from apps.grafana.installer import GrafanaInstaller
from apps.grafana.updater import GrafanaUpdater


MANIFEST = {
    # Identity
    'name': 'grafana',
    'display_name': 'Grafana',
    'description': 'Monitoring and observability platform',
    'icon': '📊',
    'version': '1.1.0',

    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },

    # Classes
    'installer_class': GrafanaInstaller,
    'updater_class': GrafanaUpdater,

    # Resources
    'default_ports': [3000],
    'volumes': ['grafana_data'],
    'networks': [],

    # Hooks
    'hooks': {
        'backup': 'apps.grafana.hooks.backup_grafana.backup_grafana',
        'restore': 'apps.grafana.hooks.restore_grafana.restore_grafana',
        'ready_check': 'apps.grafana.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.grafana.hooks.success_message.get_success_message'
    }
}
