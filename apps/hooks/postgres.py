import subprocess
import time
from datetime import datetime
from pathlib import Path

_ORCHIX_ROOT = Path(__file__).parent.parent.parent
BACKUP_DIR = _ORCHIX_ROOT / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)


def _get_meta_path(backup_path: Path) -> Path:
    name = backup_path.name
    if name.endswith('.sql'):
        return backup_path.parent / f"{name[:-4]}.meta"
    return backup_path.with_suffix('.meta')


def _get_compose_sidecar_path(backup_path: Path) -> Path:
    name = backup_path.name
    if name.endswith('.sql'):
        return backup_path.parent / f"{name[:-4]}.compose.yml"
    return backup_path.with_suffix('.compose.yml')


def _wait_for_postgres(container_name: str, timeout: int = 60) -> bool:
    for _ in range(timeout):
        r = subprocess.run(
            ['docker', 'exec', container_name, 'pg_isready', '-U', 'postgres'],
            capture_output=True
        )
        if r.returncode == 0:
            return True
        time.sleep(1)
    return False


def backup(container_name: str) -> bool:
    """Backup PostgreSQL using pg_dumpall (logical dump, safe on running container)."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{container_name}_{timestamp}.sql"
        backup_path = BACKUP_DIR / backup_name

        result = subprocess.run(
            ['docker', 'exec', '-u', 'postgres', container_name, 'pg_dumpall'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            return False

        backup_path.write_text(result.stdout, encoding='utf-8')

        meta_path = _get_meta_path(backup_path)
        with open(meta_path, 'w') as f:
            f.write(f"container: {container_name}\n")
            f.write(f"app_type: postgres\n")
            f.write(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"format: sql_dump\n")

        compose_src = _ORCHIX_ROOT / f"docker-compose-{container_name}.yml"
        if compose_src.exists():
            import shutil
            shutil.copy2(compose_src, _get_compose_sidecar_path(backup_path))

        return True
    except Exception:
        return False


def restore(backup_file: Path, container_name: str) -> bool:
    """Restore PostgreSQL from pg_dumpall SQL dump."""
    try:
        import shutil

        compose_dest = _ORCHIX_ROOT / f"docker-compose-{container_name}.yml"
        compose_sidecar = _get_compose_sidecar_path(backup_file)
        if compose_sidecar.exists():
            shutil.copy2(compose_sidecar, compose_dest)

        # Stop and clear the data volume so PostgreSQL re-initializes fresh
        subprocess.run(['docker', 'stop', container_name], capture_output=True)

        # Clear the data volume via alpine
        r = subprocess.run(
            ['docker', 'inspect', container_name, '--format',
             '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}\n{{end}}{{end}}'],
            capture_output=True, text=True
        )
        data_vol = None
        if r.returncode == 0:
            vols = [v.strip() for v in r.stdout.strip().splitlines() if v.strip()]
            if vols:
                data_vol = vols[0]

        if data_vol:
            subprocess.run(
                ['docker', 'run', '--rm', '-v', f'{data_vol}:/data',
                 'alpine', 'sh', '-c', 'rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null'],
                capture_output=True
            )

        # Start fresh container so PostgreSQL initializes the data dir
        from utils.docker_utils import ensure_orchix_network
        ensure_orchix_network()
        subprocess.run(
            ['docker', 'compose', '-f', str(compose_dest), 'up', '-d'],
            capture_output=True
        )

        if not _wait_for_postgres(container_name, timeout=60):
            return False

        # Restore SQL dump
        with open(backup_file, 'r', encoding='utf-8') as f:
            rr = subprocess.run(
                ['docker', 'exec', '-i', '-u', 'postgres', container_name, 'psql'],
                stdin=f, capture_output=True, text=True
            )

        return rr.returncode == 0
    except Exception:
        return False
