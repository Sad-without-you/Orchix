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
