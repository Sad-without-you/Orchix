import subprocess
import os
from cli.ui import show_step_detail
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


def update_vaultwarden(instance_name='vaultwarden'):
    '''
    Update Vaultwarden to latest version

    Args:
        instance_name: Name of the instance to update

    Returns:
        True if successful, False otherwise
    '''
    compose_file = f"docker-compose-{instance_name}.yml"

    if not os.path.exists(compose_file):
        show_step_detail(f"Compose file not found: {compose_file}")
        return False

    try:
        # Pull latest image
        result = run_docker_with_progress(
            ['docker', 'compose', '-f', compose_file, 'pull'],
            "Pulling latest Vaultwarden image",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            show_step_detail(f"Pull failed: {result.stderr}")
            return False

        # Restart with new image
        result = run_docker_with_progress(
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            "Restarting container with new image",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            show_step_detail(f"Restart failed: {result.stderr}")
            return False

        show_step_detail("Update completed successfully!")
        return True

    except Exception as e:
        show_step_detail(f"Update failed: {e}")
        return False
