# ORCHIX v1.1
'''Restore hook for Nginx Proxy Manager'''

import subprocess
from pathlib import Path
from cli.ui import show_info, show_success, show_error


def restore_nginx(backup_file: Path, container_name: str) -> bool:
    '''Restore Nginx Proxy Manager from backup'''
    show_info(f"Restoring Nginx Proxy Manager to {container_name}...")
    
    if backup_file.suffix == '.zip':
        return _restore_volume_windows(backup_file, container_name)
    else:
        return _restore_volume_linux(backup_file, container_name)


def _restore_volume_linux(backup_file, container_name):
    '''Restore from tar.gz on Linux'''
    
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Restoring from tar.gz...")
    
    # Get volume names
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
    except:
        show_error("Failed to parse mounts")
        return False
    
    # Extract backup
    import tempfile
    import tarfile
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Extract main backup
        with tarfile.open(backup_file, 'r:gz') as tar:
            tar.extractall(temp_dir)
        
        # Restore data
        if data_volume:
            data_tar = temp_dir / 'data.tar.gz'
            if data_tar.exists():
                show_info("  Restoring data...")
                
                result = subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '-v', f'{data_volume}:/data',
                        '-v', f'{temp_dir}:/backup',
                        'alpine',
                        'sh', '-c', 'rm -rf /data/* && tar xzf /backup/data.tar.gz -C /data'
                    ],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    show_success("  ✓ Data restored")
                else:
                    show_error("  ✗ Data restore failed")
        
        # Restore SSL certificates
        if letsencrypt_volume:
            letsencrypt_tar = temp_dir / 'letsencrypt.tar.gz'
            if letsencrypt_tar.exists():
                show_info("  Restoring SSL certificates...")
                
                result = subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '-v', f'{letsencrypt_volume}:/data',
                        '-v', f'{temp_dir}:/backup',
                        'alpine',
                        'sh', '-c', 'rm -rf /data/* && tar xzf /backup/letsencrypt.tar.gz -C /data'
                    ],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    show_success("  ✓ SSL certificates restored")
                else:
                    show_error("  ✗ SSL certificates restore failed")
        
        show_success("Restore complete!")
        return True
        
    finally:
        # Cleanup
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def _restore_volume_windows(backup_file, container_name):
    '''Restore from zip on Windows'''
    
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Restoring from zip...")
    
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
        
        # Restore data
        if data_volume:
            data_dir = temp_dir / 'data'
            if data_dir.exists():
                show_info("  Restoring data...")
                
                docker_temp_path = str(data_dir).replace('\\', '/')
                
                result = subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '-v', f'{data_volume}:/data',
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
                    show_success("  ✓ Data restored")
        
        # Restore SSL certificates
        if letsencrypt_volume:
            letsencrypt_dir = temp_dir / 'letsencrypt'
            if letsencrypt_dir.exists():
                show_info("  Restoring SSL certificates...")
                
                docker_temp_path = str(letsencrypt_dir).replace('\\', '/')
                
                result = subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '-v', f'{letsencrypt_volume}:/data',
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
                    show_success("  ✓ SSL certificates restored")
        
        show_success("Restore complete!")
        return True
        
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