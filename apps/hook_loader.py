# ORCHIX v1.1
import importlib
from typing import Callable, Optional, Any


class HookLoader:
    '''Load and execute app hooks dynamically'''
    
    @staticmethod
    def load_hook(hook_path: str) -> Optional[Callable]:
        '''Load a hook function from module path'''
        try:
            # Split module and function
            parts = hook_path.rsplit('.', 1)
            if len(parts) != 2:
                return None
            
            module_path, function_name = parts
            
            # Import module
            module = importlib.import_module(module_path)
            
            # Get function
            if hasattr(module, function_name):
                return getattr(module, function_name)
            
            return None
            
        except (ImportError, AttributeError) as e:
            print(f"Failed to load hook {hook_path}: {e}")
            return None
    
    @staticmethod
    def execute_hook(manifest: dict, hook_name: str, *args, **kwargs) -> Any:
        '''Execute a hook if it exists'''
        hooks = manifest.get('hooks', {})
        hook_path = hooks.get(hook_name)
        
        if not hook_path:
            return None
        
        hook_fn = HookLoader.load_hook(hook_path)
        if hook_fn:
            try:
                return hook_fn(*args, **kwargs)
            except Exception as e:
                print(f"Hook {hook_name} failed: {e}")
                return None
        
        return None
    
    @staticmethod
    def has_hook(manifest: dict, hook_name: str) -> bool:
        '''Check if app has a specific hook'''
        hooks = manifest.get('hooks', {})
        return hook_name in hooks


# Global instance
_hook_loader = HookLoader()


def get_hook_loader():
    '''Get global hook loader instance'''
    return _hook_loader