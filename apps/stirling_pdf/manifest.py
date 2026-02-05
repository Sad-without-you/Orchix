# ORCHIX v1.1
from apps.stirling_pdf.installer import StirlingPdfInstaller
from apps.stirling_pdf.updater import StirlingPdfUpdater

MANIFEST = {
    # Identity
    'name': 'stirling PDF',
    'display_name': 'Stirling PDF tool',
    'description': 'Free and open-source PDF tool',
    'icon': '📄',
    'version': '1.1.0',
    
    # Dependencies
    'requires': {
        'system': ['docker'],
        'containers': []
    },
    
    # Classes
    'installer_class': StirlingPdfInstaller,
    'updater_class': StirlingPdfUpdater,
    
    # Resources
    'default_ports': [8080],
    'volumes': ['stirling_pdf_logs'],
    'networks': [],
    
    # ✨ Hooks
    'hooks': {
        'backup': 'apps.stirling_pdf.hooks.backup_stirling_pdf.backup_stirling_pdf',
        'restore': 'apps.stirling_pdf.hooks.restore_stirling_pdf.restore_stirling_pdf',
        'ready_check': 'apps.stirling_pdf.hooks.ready_check.wait_for_ready',
        'success_message': 'apps.stirling_pdf.hooks.success_message.get_success_message'
    }
}
