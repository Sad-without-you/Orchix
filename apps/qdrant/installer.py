from apps.installer_base import BaseInstaller
import subprocess
import secrets
import os
from cli.ui import show_step_detail, show_step_line, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class QdrantInstaller(BaseInstaller):
    '''Installer for Qdrant vector database'''

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
        '''Get Qdrant configuration from user'''

        show_step_detail("Configure Qdrant vector database")
        show_step_line()

        config = {}

        # HTTP Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]
        config['grpc_port'] = self.manifest['default_ports'][1]

        # API Key
        api_key_choice = step_select(
            "API Key",
            [
                "🔐 Auto-generate (recommended)",
                "✏️  Enter custom API key",
                "🔓 No API key (insecure!)"
            ]
        )

        if "custom" in api_key_choice:
            api_key = step_input("Enter API key: ").strip()
            config['api_key'] = api_key if api_key else secrets.token_urlsafe(32)
        elif "No API key" in api_key_choice:
            config['api_key'] = None
        else:
            config['api_key'] = secrets.token_urlsafe(32)

        if config['api_key']:
            show_step_detail(f"API key: {config['api_key']}")

        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install Qdrant using Docker Compose'''

        instance_name = config.get('instance_name', 'qdrant')
        compose_file = f"docker-compose-{instance_name}.yml"

        try:
            # Generate compose file
            compose_content = self._generate_compose(config)

            # Write to file
            with open(compose_file, 'w') as f:
                f.write(compose_content)

            # Run docker compose
            result = run_docker_with_progress(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                f"Starting {instance_name} container"
            )

            if result.returncode != 0:
                error_output = filter_docker_errors(result.stderr)
                if error_output:
                    show_step_detail(f"Docker error: {error_output}")

                # CLEANUP
                try:
                    if os.path.exists(compose_file):
                        os.remove(compose_file)
                        show_step_detail(f"Cleaned up {compose_file}")
                except Exception as cleanup_error:
                    show_step_detail(f"Could not cleanup: {cleanup_error}")

                return False

            return True

        except Exception as e:
            show_step_detail(f"Installation failed: {e}")

            # CLEANUP
            try:
                if os.path.exists(compose_file):
                    os.remove(compose_file)
                    show_step_detail(f"Cleaned up {compose_file}")
            except Exception as cleanup_error:
                show_step_detail(f"Could not cleanup: {cleanup_error}")

            return False

    def _generate_compose(self, config):
        '''Generate docker-compose.yml content'''

        instance_name = config.get('instance_name', 'qdrant')
        volume_name = config.get('volume_name', 'qdrant_storage')

        compose_lines = [
            "services:",
            f"  {instance_name}:",
            "    image: qdrant/qdrant:latest",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:6333",
            f"      - {config['grpc_port']}:6334"
        ]

        # Environment variables
        if config.get('api_key'):
            compose_lines.extend([
                "    environment:",
                f"      - QDRANT__SERVICE__API_KEY={config['api_key']}"
            ])

        # Volumes
        compose_lines.extend([
            "    volumes:",
            f"      - {volume_name}:/qdrant/storage",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ])

        return '\n'.join(compose_lines)
