from apps.installer_base import BaseInstaller
import subprocess
import os
from cli.ui import show_step_detail, show_step_line, step_input
from utils.docker_progress import run_docker_with_progress, filter_docker_errors

class JellyfinInstaller(BaseInstaller):
    '''Installer for Jellyfin Media Server'''
    
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
        '''Get Jellyfin configuration from user'''
        show_step_detail("Configure Jellyfin Media Server")
        show_step_line()

        config = {}

        # HTTP Port
        default_http = 8096
        http_port = step_input(f"HTTP Port (default: {default_http}): ").strip()
        config['http_port'] = int(http_port) if http_port else default_http

        # HTTPS Port
        default_https = 8920
        https_port = step_input(f"HTTPS Port (default: {default_https}): ").strip()
        config['https_port'] = int(https_port) if https_port else default_https

        show_step_detail("Configuration complete!")
        return config
    
    def install(self, config, instance_name=None):
        '''Install Jellyfin'''
        instance_name = config.get('instance_name', 'jellyfin')

        # Generate docker-compose file
        compose_content = self._generate_compose(config)
        compose_file = f"docker-compose-{instance_name}.yml"

        with open(compose_file, 'w') as f:
            f.write(compose_content)

        # Start container with progress indicator
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
        instance_name = config.get('instance_name', 'jellyfin')
        http_port = config.get('http_port', 8096)
        https_port = config.get('https_port', 8920)
        
        compose = f"""services:
  {instance_name}:
    image: jellyfin/jellyfin:latest
    container_name: {instance_name}
    restart: unless-stopped
    ports:
      - "{http_port}:8096"
      - "{https_port}:8920"
      - "7359:7359/udp"
      - "1900:1900/udp"
    volumes:
      - {instance_name}_config:/config
      - {instance_name}_cache:/cache
    environment:
      - TZ=Europe/Berlin

volumes:
  {instance_name}_config:
  {instance_name}_cache:
"""
        return compose