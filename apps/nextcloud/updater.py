from apps.updater_base import BaseUpdater
import subprocess
import os
from cli.ui import show_step_detail
from utils.docker_progress import run_docker_with_progress, filter_docker_errors

class NextcloudUpdater(BaseUpdater):
    '''Updater for Nextcloud Cloud Storage'''
    
    def get_available_actions(self):
        '''Nextcloud supports version updates'''
        return ['version_update']
    
    def version_update(self):
        '''Update Nextcloud to latest version'''
        try:
            container_name = self.app_name
            compose_file = self._find_compose_file(container_name)
            
            # Pull latest image
            result = run_docker_with_progress(
                ['docker', 'pull', 'nextcloud:latest'],
                "Pulling nextcloud:latest",
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                show_step_detail(f"Pull failed: {result.stderr}")
                return False
            
            # Restart container with new image
            if compose_file:
                subprocess.run(
                    ['docker', 'compose', '-f', compose_file, 'down'],
                    capture_output=True,
                    text=True
                )

                result = run_docker_with_progress(
                    ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                    "Restarting container with new image",
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    show_step_detail("Nextcloud updated successfully!")
                    return True
            
            return False
        except Exception as e:
            show_step_detail(f"Update failed: {e}")
            return False