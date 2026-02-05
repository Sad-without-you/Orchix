from apps.updater_base import BaseUpdater
import subprocess
import os
from cli.ui import show_warning, show_step_detail, step_input
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class PostgresUpdater(BaseUpdater):
    '''Updater for PostgreSQL database'''
    
    def get_available_actions(self):
        '''PostgreSQL only supports minor version updates (DANGEROUS!)'''
        return ['version_update']
    
    def version_update(self):
        '''
        Update PostgreSQL to latest MINOR version
        WARNING: Major version updates require manual migration!
        '''
        try:
            show_warning("⚠️  DATABASE UPDATE WARNING!")
            show_step_detail("This will update to latest MINOR version only")
            show_step_detail("Major version updates require manual migration with pg_dump/restore")

            # Confirm
            confirm = step_input("Continue with minor version update? (yes/NO): ").strip().lower()
            if confirm != 'yes':
                show_step_detail("Update cancelled")
                return False
            
            container_name = self.app_name
            compose_file = self._find_compose_file(container_name)
            
            if not compose_file:
                show_step_detail(f"Compose file not found for {container_name}")
                return False
            
            # Read compose to get current version
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_content = f.read()
            
            # Extract current version
            current_version = '16'  # default
            for line in compose_content.split('\n'):
                if 'image: postgres:' in line:
                    current_version = line.split(':')[-1].strip()
                    break
            
            # Pull latest minor version
            result = run_docker_with_progress(
                ['docker', 'pull', f'postgres:{current_version}'],
                f"Pulling postgres:{current_version} (latest minor)",
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                show_step_detail(f"Pull failed: {result.stderr}")
                return False
            
            # Stop and remove old container
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
            
            # Recreate container
            result = run_docker_with_progress(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                "Starting container with new version",
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