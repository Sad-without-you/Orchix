from apps.installer_base import BaseInstaller
import subprocess
import secrets
import os
from cli.ui import show_step_detail, show_step_line, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class GrafanaInstaller(BaseInstaller):
    '''Installer for Grafana monitoring platform'''

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
        '''Get Grafana configuration from user'''

        show_step_detail("Configure Grafana monitoring platform")
        show_step_line()

        config = {}

        # Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]

        # Admin User
        default_user = 'admin'
        admin_user = step_input(f"Admin username (default: {default_user}): ").strip()
        config['admin_user'] = admin_user if admin_user else default_user

        # Admin Password
        pwd_choice = step_select(
            "Admin Password",
            [
                "🔐 Auto-generate (recommended)",
                "✏️  Enter custom password"
            ]
        )

        if "custom" in pwd_choice:
            password = step_input("Enter password: ").strip()
            config['admin_password'] = password if password else secrets.token_urlsafe(16)
        else:
            config['admin_password'] = secrets.token_urlsafe(16)

        show_step_detail(f"Admin password: {config['admin_password']}")

        # Anonymous Access
        anon_choice = step_select(
            "Anonymous Access",
            [
                "❌ Disabled (recommended)",
                "✅ Enabled"
            ]
        )

        config['anonymous_enabled'] = "Enabled" in anon_choice

        # Timezone
        default_tz = 'Europe/Berlin'
        timezone = step_input(f"Timezone (default: {default_tz}): ").strip()
        config['timezone'] = timezone if timezone else default_tz

        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install Grafana using Docker Compose'''

        instance_name = config.get('instance_name', 'grafana')
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

        instance_name = config.get('instance_name', 'grafana')
        volume_name = config.get('volume_name', 'grafana_data')

        compose_lines = [
            "services:",
            f"  {instance_name}:",
            "    image: grafana/grafana:latest",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:3000",
            "    environment:",
            f"      - GF_SECURITY_ADMIN_USER={config.get('admin_user', 'admin')}",
            f"      - GF_SECURITY_ADMIN_PASSWORD={config['admin_password']}",
            f"      - GF_AUTH_ANONYMOUS_ENABLED={str(config.get('anonymous_enabled', False)).lower()}",
            f"      - TZ={config.get('timezone', 'Europe/Berlin')}",
            "    volumes:",
            f"      - {volume_name}:/var/lib/grafana",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ]

        return '\n'.join(compose_lines)
