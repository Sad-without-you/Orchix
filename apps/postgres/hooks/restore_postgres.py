# ORCHIX v1.1
'''Restore hook for PostgreSQL'''

import subprocess
from pathlib import Path
from cli.ui import show_info, show_success, show_error


def restore_postgres(backup_file: Path, container_name: str) -> bool:
    '''Restore PostgreSQL database from backup'''
    show_info("Restoring PostgreSQL database...")
    
    # Read backup file
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        show_error(f"Failed to read backup: {e}")
        return False
    
    # Execute SQL via psql
    result = subprocess.run(
        [
            'docker', 'exec', '-i', container_name,
            'psql', '-U', 'postgres'
        ],
        input=sql_content,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode == 0:
        show_success("Database restored!")
        return True
    else:
        show_error(f"Restore failed: {result.stderr}")
        return False