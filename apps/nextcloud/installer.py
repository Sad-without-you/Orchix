from apps.installer_base import BaseInstaller
import subprocess
import os
from cli.ui import show_step_detail, show_step_line, step_input
from utils.docker_progress import run_docker_with_progress, filter_docker_errors

class NextcloudInstaller(BaseInstaller):
    '''Installer for Nextcloud Cloud Storage'''
    
    def check_dependencies(self):
        '''Check if Docker is available'''
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_configuration(self, instance_name=None):
        '''Get Nextcloud configuration from user'''
        show_step_detail("Configure Nextcloud Cloud Storage")
        show_step_line()

        config = {}

        # Port configuration is handled by install_menu.py
        # Set default port for install menu to use
        config['port'] = 8080

        show_step_detail("Configuration complete!")
        return config
    
    def install(self, config, instance_name=None):
        '''Install Nextcloud'''
        instance_name = config.get('instance_name', 'nextcloud')

        # Generate docker-compose file
        compose_content = self._generate_compose(config)
        compose_file = f"docker-compose-{instance_name}.yml"

        with open(compose_file, 'w') as f:
            f.write(compose_content)

        # Start container with progress display
        result = run_docker_with_progress(
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            f"Pulling and starting {instance_name} container"
        )

        if result.returncode != 0:
            show_step_detail(f"Installation failed with exit code: {result.returncode}")
            return False

        return True
    
    def _generate_compose(self, config):
        '''Generate docker-compose content'''
        instance_name = config.get('instance_name', 'nextcloud')
        port = config.get('port', 8085)
        
        compose = f"""services:
  {instance_name}:
    image: nextcloud:latest
    container_name: {instance_name}
    restart: unless-stopped
    ports:
      - "{port}:80"
    volumes:
      - {instance_name}_data:/var/www/html
    environment:
      - SQLITE_DATABASE=nextcloud

volumes:
  {instance_name}_data:
"""
        return compose