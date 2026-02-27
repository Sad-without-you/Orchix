# ORCHIX v1.4
from abc import ABC, abstractmethod


class BaseInstaller(ABC):
    '''
    Base class for all app installers
    Every app installer must inherit from this
    '''
    
    def __init__(self, manifest):
        '''Initialize installer with app manifest'''
        self.manifest = manifest
        self.app_name = manifest['name']
    
    @abstractmethod
    def check_dependencies(self):
        '''Check if system has required dependencies'''
        pass  # Subclass MUST implement!
    
    @abstractmethod
    def get_configuration(self):
        '''Get configuration from user '''
        pass  # Subclass MUST implement!
    
    @abstractmethod
    def install(self, config):
        '''Install the application'''
        pass  # Subclass MUST implement!
    
    def verify_installation(self):
        '''Verify installation was successful (optional) '''
        # Default implementation - subclass can override
        return True