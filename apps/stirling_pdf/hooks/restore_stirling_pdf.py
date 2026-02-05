# ORCHIX v1.1
'''Restore hook for Stirling PDF'''

import subprocess
from pathlib import Path
from cli.ui import show_info, show_success, show_error


def restore_stirling_pdf(backup_file, container_name: str = None) -> bool:
    '''Restore Stirling PDF from backup'''
    # Handle parameter swap - if backup_file is a string and container_name is a Path, swap them
    if isinstance(backup_file, str) and hasattr(container_name, 'suffix'):
        backup_file, container_name = container_name, backup_file
    
    # Convert to Path if string
    if isinstance(backup_file, str):
        from pathlib import Path
        backup_file = Path(backup_file)
    
    show_info(f"Restoring to {container_name}...")
    
    if backup_file.suffix == '.zip':
        return _restore_volume_windows(backup_file, container_name)
    else:
        return _restore_volume_linux(backup_file, container_name)


def _restore_volume_linux(backup_file, container_name):
    '''Restore from tar.gz on Linux'''
    
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Restoring from tar.gz...")
    
    # Get volume name
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{json .Mounts}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_error("Failed to inspect container")
        return False
    
    import json
    try:
        mounts = json.loads(result.stdout)
        volume_name = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume' and 'logs' in mount.get('Name', ''):
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No logs volume found!")
            return False
    except:
        show_error("Failed to parse mounts")
        return False
    
    # Extract tar
    result = subprocess.run(
        [
            'docker', 'run', '--rm',
            '-v', f'{volume_name}:/data',
            '-v', f'{BACKUP_DIR.absolute()}:/backup',
            'alpine',
            'sh', '-c', f'rm -rf /data/* && tar xzf /backup/{backup_file.name} -C /data'
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        show_success("Volume restored!")
        return True
    else:
        show_error(f"Restore failed: {result.stderr}")
        return False


def _restore_volume_windows(backup_file, container_name):
    '''Restore from zip on Windows'''
    
    from cli.backup_menu import BACKUP_DIR
    import os
    import tempfile
    import shutil
    import zipfile
    
    show_info("Restoring from zip...")
    
    # Get volume name
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{json .Mounts}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_error("Failed to inspect container")
        return False
    
    import json
    try:
        mounts = json.loads(result.stdout)
        volume_name = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume' and 'logs' in mount.get('Name', ''):
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No logs volume found!")
            return False
    except:
        show_error("Failed to parse mounts")
        return False
    
    try:
        temp_dir = Path(tempfile.mkdtemp())
        
        # Extract zip
        show_info("Extracting zip file...")
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        docker_temp_path = str(temp_dir).replace('\\', '/')
        
        # Copy to volume
        result = subprocess.run(
            [
                'docker', 'run', '--rm',
                '-v', f'{volume_name}:/data',
                '-v', f'{docker_temp_path}:/backup',
                'alpine',
                'sh', '-c', 'rm -rf /data/* && cp -r /backup/* /data/'
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            show_success("Volume restored!")
            return True
        else:
            show_error(f"Restore failed: {result.stderr}")
            return False
    
    except Exception as e:
        show_error(f"Restore failed: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass
