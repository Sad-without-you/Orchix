# ORCHIX v1.1
'''Backup hook for PostgreSQL'''

import subprocess
from pathlib import Path
from datetime import datetime
from cli.ui import show_info, show_success, show_error


def backup_postgres(container_name: str) -> bool:
    '''Backup PostgreSQL database using pg_dump'''
    from cli.backup_menu import BACKUP_DIR
    
    show_info("Creating PostgreSQL database backup...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{container_name}_{timestamp}.sql"
    
    # Use pg_dumpall for complete backup
    result = subprocess.run(
        [
            'docker', 'exec', container_name,
            'pg_dumpall', '-U', 'postgres'
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        # Write to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        show_success(f"Database backed up to: {backup_file.name}")
        _create_metadata(container_name, backup_file)
        return True
    else:
        show_error(f"Backup failed: {result.stderr}")
        return False


def _create_metadata(container_name, backup_file):
    '''Create metadata file for backup'''
    
    from cli.backup_menu import create_metadata
    create_metadata(container_name, backup_file, 'postgres')