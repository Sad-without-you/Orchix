import subprocess


def get_docker_compose_command():
    """Get the correct docker compose command for the system"""

    try:
        # Try new format: docker compose (Docker 20.10+)
        result = subprocess.run(
            ['docker', 'compose', '--version'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return ['docker', 'compose']

        # Fallback to old format: docker-compose (legacy)
        result = subprocess.run(
            ['docker-compose', '--version'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return ['docker-compose']
    except FileNotFoundError:
        pass

    # Default to new format (will provide helpful error if neither available)
    return ['docker', 'compose']


def safe_docker_run(command, **kwargs):
    """Run a docker command safely - returns None if Docker is not installed."""
    try:
        return subprocess.run(command, **kwargs)
    except FileNotFoundError:
        return None


def check_docker_status():
    """Check Docker availability and return detailed status."""
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {'installed': True, 'running': True, 'message': 'Docker is running'}
        else:
            # Docker installed but daemon not running
            stderr = result.stderr.lower()
            if 'cannot connect' in stderr or 'is the docker daemon running' in stderr:
                return {'installed': True, 'running': False, 'message': 'Docker is installed but not running. Start Docker Desktop or the Docker service.'}
            return {'installed': True, 'running': False, 'message': f'Docker error: {result.stderr.strip()[:100]}'}
    except FileNotFoundError:
        return {'installed': False, 'running': False, 'message': 'Docker is not installed. Use Setup > Install Docker.'}
    except subprocess.TimeoutExpired:
        return {'installed': True, 'running': False, 'message': 'Docker is not responding (timeout). Restart Docker.'}


ORCHIX_NETWORK = 'orchix'


def ensure_orchix_network():
    """Create the global orchix network and connect all running ORCHIX containers."""
    try:
        from pathlib import Path

        # Create network if it doesn't exist
        inspect = subprocess.run(
            ['docker', 'network', 'inspect', ORCHIX_NETWORK],
            capture_output=True
        )
        if inspect.returncode != 0:
            subprocess.run(
                ['docker', 'network', 'create', ORCHIX_NETWORK],
                capture_output=True
            )

        # Connect all running ORCHIX containers (those with a compose file in CWD)
        ps = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True, text=True
        )
        if ps.returncode != 0:
            return

        for name in ps.stdout.strip().splitlines():
            if not name:
                continue
            if Path(f'docker-compose-{name}.yml').exists():
                subprocess.run(
                    ['docker', 'network', 'connect', ORCHIX_NETWORK, name],
                    capture_output=True
                )
    except Exception:
        pass


def resolve_container_uid(container_name: str) -> str:
    """Resolve the numeric UID a container runs as.

    Returns the UID as a string, or '0' if it cannot be determined or runs as root.
    Used by backup/restore to fix file ownership after volume extraction.
    """
    try:
        insp = subprocess.run(
            ['docker', 'inspect', container_name,
             '--format', '{{.Config.Image}}\n{{.Config.User}}'],
            capture_output=True, text=True
        )
        if insp.returncode != 0:
            return '0'
        lines = insp.stdout.strip().splitlines()
        if len(lines) < 2:
            return '0'
        image, cuser = lines[0].strip(), lines[1].strip()
        if not cuser or cuser in ('', 'root', '0'):
            return '0'
        if cuser.isdigit():
            return cuser
        # Named user: resolve via a quick container run using the same image
        uid_r = subprocess.run(
            ['docker', 'run', '--rm', '--entrypoint', 'id', image, '-u', cuser],
            capture_output=True, text=True
        )
        if uid_r.returncode == 0 and uid_r.stdout.strip().isdigit():
            return uid_r.stdout.strip()
    except Exception:
        pass
    return '0'

