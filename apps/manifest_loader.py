# ORCHIX v1.1
import importlib
from pathlib import Path


def load_manifest(app_name):
    ''' load_manifest(app_name) -> dict'''
    try:
        # Build module name
        module_name = f'apps.{app_name}.manifest'
        
        # Import
        module = importlib.import_module(module_name)
        
        # Check if MANIFEST exists
        if hasattr(module, 'MANIFEST'):
            return module.MANIFEST
        else:
            raise ValueError(f"No MANIFEST in {module_name}")
    
    except ModuleNotFoundError:
        # app does not exist
        raise ValueError(f"App '{app_name}' not found")
    
    except Exception as e:
        # Other errors
        raise ValueError(f"Error loading {app_name}: {e}")


def discover_apps():
    '''Discover all available apps'''
    
    # 1. Get apps directory
    apps_dir = Path('apps')
    
    # 2. Create empty list
    apps = []
    
    # 3. Iterate through items
    for item in apps_dir.iterdir():
        
        # 4. Check if directory
        if item.is_dir():
            
            # 5. Exclude special dirs
            if item.name not in ['__pycache__', 'generic']:
                
                # 6. Check if has manifest.py
                if (item / 'manifest.py').exists():
                    
                    # 7. Add to list
                    apps.append(item.name)
    
    # 8. Return sorted
    return sorted(apps)


def load_all_manifests():
    '''Load manifests for all discovered apps'''
    
    # 1. Create empty dict
    manifests = {}
    
    # 2. Discover all apps
    apps = discover_apps()
    
    # 3. Loop through apps
    for app_name in apps:
        try:
            # 4. Load manifest
            manifest = load_manifest(app_name)
            
            # 5. Save to dict
            manifests[app_name] = manifest
            
        except Exception as e:
            # 6. Handle errors (print warning, continue)
            print(f"Warning: Could not load {app_name}: {e}")
    
    # 7. Return dict
    return manifests
