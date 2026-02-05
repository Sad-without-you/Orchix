# ORCHIX v1.1
from apps.updater_base import BaseUpdater


class NginxUpdater(BaseUpdater):
    '''Updater for Nginx Proxy Manager'''
    
    def get_update_info(self):
        '''Get update information'''
        return {
            'backup_recommended': True,
            'downtime_expected': True,
            'breaking_changes': False
        }