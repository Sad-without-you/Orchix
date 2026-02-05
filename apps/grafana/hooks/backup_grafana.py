# ORCHIX v1.1
import subprocess
import os
from datetime import datetime


def backup_grafana(container_name: str, backup_dir: str) -> bool:
    '''Backup Grafana data'''
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'grafana_backup_{timestamp}.tar.gz')

        # Create backup using docker cp
        result = subprocess.run(
            ['docker', 'exec', container_name, 'tar', 'czf', '/tmp/grafana-backup.tar.gz', '/var/lib/grafana'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Backup creation failed: {result.stderr}")
            return False

        # Copy backup out of container
        result = subprocess.run(
            ['docker', 'cp', f'{container_name}:/tmp/grafana-backup.tar.gz', backup_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Backup copy failed: {result.stderr}")
            return False

        # Cleanup temp file
        subprocess.run(
            ['docker', 'exec', container_name, 'rm', '/tmp/grafana-backup.tar.gz'],
            capture_output=True,
            text=True
        )

        print(f"Backup saved to: {backup_file}")
        return True

    except Exception as e:
        print(f"Backup failed: {e}")
        return False
