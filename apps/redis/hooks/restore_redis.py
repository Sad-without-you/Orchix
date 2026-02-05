# ORCHIX v1.1
'''Restore hook for Redis'''

import subprocess
from pathlib import Path
from cli.ui import show_info, show_success, show_error


def restore_redis(backup_file: Path, container_name: str) -> bool:
    '''Restore Redis from backup'''
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
            if mount.get('Type') == 'volume':
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No volume found!")
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
            if mount.get('Type') == 'volume':
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No volume found!")
            return False
    except:
        show_error("Failed to parse mounts")
        return False
    
    temp_dir = BACKUP_DIR.absolute() / f"restore_{container_name}"
    
    try:
        # Extract zip
        show_info("Extracting zip archive...")
        import zipfile
        
        temp_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Copy to volume
        show_info("Copying to volume...")
        
        docker_temp_path = str(temp_dir).replace('\\', '/')
        
        result = subprocess.run(
            [
                'docker', 'run', '--rm',
                '-v', f'{volume_name}:/data',
                '-v', f'{docker_temp_path}:/backup',
                'alpine',
                'sh', '-c', 'rm -rf /data/* && cp -r /backup/* /data/ || cp -r /backup/. /data/'
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
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass