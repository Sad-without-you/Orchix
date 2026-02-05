# ORCHIX v1.1
import subprocess
from pathlib import Path
from datetime import datetime
from cli.ui import show_info, show_success, show_error


def backup_jellyfin(container_name: str) -> bool:
    '''Backup Jellyfin configuration and cache'''
    from cli.backup_menu import BACKUP_DIR
    from utils.system import is_windows
    
    show_info("Using volume backup for Jellyfin...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if is_windows():
        backup_file = BACKUP_DIR / f"{container_name}_{timestamp}.zip"
        return _backup_volume_windows(container_name, backup_file)
    else:
        backup_file = BACKUP_DIR / f"{container_name}_{timestamp}.tar.gz"
        return _backup_volume_linux(container_name, backup_file)


def _backup_volume_linux(container_name, backup_file):
    '''Backup volume on Linux using tar'''
    
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Creating volume backup (tar.gz)...")
    
    # Get volume name dynamically
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{json .Mounts}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_error(f"Failed to inspect container: {result.stderr}")
        return False
    
    # Parse volume name
    import json
    try:
        mounts = json.loads(result.stdout)
        volume_name = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume' and 'config' in mount.get('Name', ''):
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No config volume found!")
            return False
        
        show_info(f"→ Using volume: {volume_name}")
        
    except json.JSONDecodeError as e:
        show_error(f"Failed to parse mounts: {e}")
        return False
    
    # Create tar backup
    result = subprocess.run(
        [
            'docker', 'run', '--rm',
            '-v', f'{volume_name}:/data',
            '-v', f'{BACKUP_DIR.absolute()}:/backup',
            'alpine',
            'tar', 'czf', f'/backup/{backup_file.name}', '-C', '/data', '.'
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        show_success(f"Volume backed up to: {backup_file.name}")
        _create_metadata(container_name, backup_file)
        return True
    else:
        show_error(f"Backup failed: {result.stderr}")
        return False


def _backup_volume_windows(container_name, backup_file):
    '''Backup volume on Windows using zip'''
    
    from cli.backup_menu import BACKUP_DIR
    import tempfile
    import shutil
    import os
    
    show_info("Creating volume backup (zip)...")
    
    # Get volume name
    result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{json .Mounts}}'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_error(f"Failed to inspect container: {result.stderr}")
        return False
    
    # Parse volume name
    import json
    try:
        mounts = json.loads(result.stdout)
        volume_name = None
        
        for mount in mounts:
            if mount.get('Type') == 'volume' and 'config' in mount.get('Name', ''):
                volume_name = mount.get('Name')
                break
        
        if not volume_name:
            show_error("No config volume found!")
            return False
        
        show_info(f"→ Using volume: {volume_name}")
        
    except json.JSONDecodeError as e:
        show_error(f"Failed to parse mounts: {e}")
        return False
    
    try:
        temp_dir = Path(tempfile.mkdtemp())
        docker_temp_path = str(temp_dir).replace('\\', '/')
        
        # Extract volume to temp
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
        
        if result.returncode != 0:
            show_error(f"Failed to extract data: {result.stderr}")
            return False
        
        # Create zip
        show_info("Creating zip archive...")
        import zipfile
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        show_success(f"Volume backed up to: {backup_file.name}")
        _create_metadata(container_name, backup_file)
        
        return True
        
    except Exception as e:
        show_error(f"Backup failed: {e}")
        return False
        
    finally:
        # Cleanup
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass


def _create_metadata(container_name, backup_file):
    '''Create metadata file for backup'''
    
    from cli.backup_menu import create_metadata
    create_metadata(container_name, backup_file, 'jellyfin')
