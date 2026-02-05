from apps.updater_base import BaseUpdater
import subprocess
import os
from cli.ui import show_step_detail
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class GrafanaUpdater(BaseUpdater):
    '''Updater for Grafana monitoring platform'''

    def get_available_actions(self):
        '''Grafana supports version updates'''
        return ['version_update']

    def version_update(self):
        '''Update Grafana to latest version'''
        try:
            container_name = self.app_name
            compose_file = self._find_compose_file(container_name)

            # Pull latest image
            result = run_docker_with_progress(
                ['docker', 'pull', 'grafana/grafana:latest'],
                "Pulling grafana/grafana:latest",
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                show_step_detail(f"Pull failed: {result.stderr}")
                return False

            # Stop and remove old container
            if compose_file:
                show_step_detail("Stopping old container...")
                subprocess.run(
                    ['docker', 'compose', '-f', compose_file, 'down'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                # Force remove
                subprocess.run(
                    ['docker', 'rm', '-f', container_name],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                # Recreate
                result = run_docker_with_progress(
                    ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                    "Starting container with new version",
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                show_step_detail("Restarting container...")
                result = subprocess.run(
                    ['docker', 'restart', container_name],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

            return result.returncode == 0

        except Exception as e:
            show_step_detail(f"Version update failed: {e}")
            return False

    def _find_compose_file(self, container_name):
        '''Find compose file for container'''
        possible_files = [
            f'docker-compose-{container_name}.yml',
            'docker-compose.yml',
            f'{container_name}-docker-compose.yml'
        ]

        for filepath in possible_files:
            if os.path.exists(filepath):
                return filepath

        return None
