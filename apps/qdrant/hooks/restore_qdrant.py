# ORCHIX v1.1
'''Restore hook for Qdrant'''

import subprocess
import os


def restore_qdrant(container_name: str, backup_file: str) -> bool:
    '''Restore Qdrant data from backup'''
    try:
        if not os.path.exists(backup_file):
            print(f"Backup file not found: {backup_file}")
            return False

        # Copy backup into container
        result = subprocess.run(
            ['docker', 'cp', backup_file, f'{container_name}:/tmp/qdrant-backup.tar.gz'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Failed to copy backup: {result.stderr}")
            return False

        # Extract backup
        result = subprocess.run(
            ['docker', 'exec', container_name, 'tar', 'xzf', '/tmp/qdrant-backup.tar.gz', '-C', '/'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Failed to extract backup: {result.stderr}")
            return False

        # Cleanup temp file
        subprocess.run(
            ['docker', 'exec', container_name, 'rm', '/tmp/qdrant-backup.tar.gz'],
            capture_output=True,
            text=True
        )

        # Restart container to apply changes
        subprocess.run(
            ['docker', 'restart', container_name],
            capture_output=True,
            text=True
        )

        print(f"Restore completed successfully")
        return True

    except Exception as e:
        print(f"Restore failed: {e}")
        return False
