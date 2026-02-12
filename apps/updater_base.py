# ORCHIX v1.2
from abc import ABC, abstractmethod
import os


class BaseUpdater(ABC):
    '''
    Base class for all app updaters
    Every app updater must inherit from this
    '''
    
    def __init__(self, manifest):
        '''Initialize updater with app manifest'''
        self.manifest = manifest
        self.app_name = manifest['name']
    
    @abstractmethod
    def get_available_actions(self):
        '''Return list of available update actions for this app'''
        pass  # Subclass MUST implement!
    
    @abstractmethod
    def version_update(self):
        '''Update app to new version'''
        pass  # Subclass MUST implement!
    
    def _find_compose_file(self, container_name):
        '''Find compose file for container'''
        possible_files = [
            f'docker-compose-{container_name}.yml',
            'docker-compose.yml',
            f'{container_name}-docker-compose.yml'
        ]
        
        for filepath in possible_files:
            if os.path.exists(filepath):
                return filepath
        
        return None