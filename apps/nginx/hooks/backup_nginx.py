# ORCHIX v1.1
'''Backup hook for Nginx Proxy Manager'''

import subprocess
from pathlib import Path
from datetime import datetime
from cli.ui import show_info, show_success, show_error, show_warning


def backup_nginx(container_name: str) -> bool:
    '''Backup Nginx Proxy Manager data and certificates'''
    from cli.backup_menu import BACKUP_DIR
    from utils.system import is_windows
    
    show_info("Backing up Nginx Proxy Manager (data + SSL certificates)...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if is_windows():
        backup_file = BACKUP_DIR / f"{container_name}_{timestamp}.zip"
        return _backup_volume_windows(container_name, backup_file)
    else:
        backup_file = BACKUP_DIR / f"{container_name}_{timestamp}.tar.gz"
        return _backup_volume_linux(container_name, backup_file)


def _backup_volume_linux(container_name, backup_file):
    '''Backup volumes on Linux using tar'''
    
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Creating volume backup (tar.gz)...")
    
    # Get volume names
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{json .Mounts}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_error(f"Failed to inspect container")
        return False
    
    import json
    try:
        mounts = json.loads(result.stdout)
        data_volume = None
        letsencrypt_volume = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume':
                name = mount.get('Name')
                dest = mount.get('Destination', '')
                
                if dest == '/data':
                    data_volume = name
                elif 'letsencrypt' in dest:
                    letsencrypt_volume = name
        
        if not data_volume and not letsencrypt_volume:
            show_error("No volumes found!")
            return False
        
        if data_volume:
            show_info(f"→ Data: {data_volume}")
        if letsencrypt_volume:
            show_info(f"→ SSL Certs: {letsencrypt_volume}")
        
    except json.JSONDecodeError as e:
        show_error(f"Failed to parse mounts: {e}")
        return False
    
    # Create tar with volumes
    volumes_to_backup = []
    if data_volume:
        volumes_to_backup.append((data_volume, 'data'))
    if letsencrypt_volume:
        volumes_to_backup.append((letsencrypt_volume, 'letsencrypt'))
    
    # Backup each volume
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        for volume_name, label in volumes_to_backup:
            show_info(f"  Backing up {label}...")
            
            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f'{volume_name}:/data',
                    '-v', f'{temp_dir}:/backup',
                    'alpine',
                    'sh', '-c', f'cd /data && tar czf /backup/{label}.tar.gz .'
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                show_error(f"Failed to backup {label}")
                return False
        
        # Combine into single archive
        import tarfile
        with tarfile.open(backup_file, 'w:gz') as tar:
            for volume_name, label in volumes_to_backup:
                tar_path = temp_dir / f"{label}.tar.gz"
                if tar_path.exists():
                    tar.add(tar_path, arcname=f"{label}.tar.gz")
        
        show_success(f"Backup created: {backup_file.name}")
        _create_metadata(container_name, backup_file)
        
        return True
        
    finally:
        # Cleanup
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def _backup_volume_windows(container_name, backup_file):
    '''Backup volumes on Windows using zip'''
    
    from cli.backup_menu import BACKUP_DIR
    import os
    
    show_info("Creating volume backup (zip)...")
    
    # Get volumes
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
        data_volume = None
        letsencrypt_volume = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume':
                name = mount.get('Name')
                dest = mount.get('Destination', '')
                
                if dest == '/data':
                    data_volume = name
                elif 'letsencrypt' in dest:
                    letsencrypt_volume = name
        
        if not data_volume and not letsencrypt_volume:
            show_error("No volumes found!")
            return False
    except:
        show_error("Failed to parse mounts")
        return False
    
    # Temp directory
    temp_dir = BACKUP_DIR.absolute() / f"temp_{container_name}"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Extract volumes
        volumes_to_backup = []
        if data_volume:
            volumes_to_backup.append((data_volume, 'data'))
        if letsencrypt_volume:
            volumes_to_backup.append((letsencrypt_volume, 'letsencrypt'))
        
        for volume_name, label in volumes_to_backup:
            show_info(f"  Extracting {label}...")
            
            vol_dir = temp_dir / label
            vol_dir.mkdir(exist_ok=True)
            
            docker_temp_path = str(vol_dir).replace('\\', '/')
            
            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f'{volume_name}:/data',
                    '-v', f'{docker_temp_path}:/backup',
                    'alpine',
                    'sh', '-c', 'cp -r /data/* /backup/ 2>/dev/null || cp -r /data/. /backup/'
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
        
        # Create zip
        show_info("Creating zip archive...")
        import zipfile
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        show_success(f"Backup created: {backup_file.name}")
        _create_metadata(container_name, backup_file)
        
        return True
        
    except Exception as e:
        show_error(f"Backup failed: {e}")
        return False
        
    finally:
        # Cleanup
        try:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass


def _create_metadata(container_name, backup_file):
    '''Create metadata file for backup'''
    
    from cli.backup_menu import create_metadata
    create_metadata(container_name, backup_file, 'nginx')