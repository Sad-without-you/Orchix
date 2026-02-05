from apps.installer_base import BaseInstaller
import subprocess
import secrets
import os
import socket
from cli.ui import show_step_detail, show_step_line, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class VaultwardenInstaller(BaseInstaller):
    '''Installer for Vaultwarden password manager'''

    def _get_local_ip(self):
        '''Get local IP address of the server'''
        try:
            # Create a socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "localhost"

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
        '''Get Vaultwarden configuration from user'''

        show_step_detail("Configure Vaultwarden password manager")
        show_step_line()

        config = {}

        # Port
        config['port'] = self.manifest['default_ports'][0]

        # Domain/Host - auto-detect
        show_step_detail("Server Configuration")
        default_host = self._get_local_ip()
        show_step_detail(f"Detected server IP: {default_host}")
        host = step_input(f"Server hostname/IP (default: {default_host}): ").strip()
        config['server_host'] = host if host else default_host

        # Signups
        signup_choice = step_select(
            "Allow new user signups",
            [
                "✅ Yes - Anyone can register",
                "🔒 No - Invite only (recommended)"
            ]
        )
        config['signups_allowed'] = "true" if "Yes" in signup_choice else "false"

        # Admin token
        show_step_line()
        show_step_detail("Admin Panel Configuration")
        show_step_detail("Admin token is required to access the admin panel at /admin")

        admin_choice = step_select(
            "Admin Panel",
            [
                "🔑 Generate random token (recommended)",
                "✏️  Enter custom token",
                "⏭️  Skip (disable admin panel)"
            ]
        )

        if "Generate" in admin_choice:
            config['admin_token'] = secrets.token_urlsafe(32)
            show_step_detail(f"Admin token: {config['admin_token']}")
            show_step_detail("SAVE THIS TOKEN! You'll need it to access /admin")
        elif "custom" in admin_choice:
            config['admin_token'] = step_input("Enter admin token: ").strip()
        else:
            config['admin_token'] = None
            show_step_detail("Admin panel will be disabled")

        # SMTP Configuration
        show_step_line()
        show_step_detail("Email Configuration (optional, for password recovery)")
        email_choice = step_select(
            "Email Setup",
            [
                "📧 Configure SMTP",
                "⏭️  Skip (no email)"
            ]
        )

        if "Configure SMTP" in email_choice:
            config['smtp_host'] = step_input("SMTP Host: ").strip()
            config['smtp_port'] = step_input("SMTP Port (default: 587): ").strip() or "587"

            smtp_security = step_select(
                "SMTP Security",
                [
                    "🔒 STARTTLS (587)",
                    "🔐 SSL/TLS (465)",
                    "⚠️  None"
                ]
            )

            if "STARTTLS" in smtp_security:
                config['smtp_security'] = "starttls"
            elif "SSL/TLS" in smtp_security:
                config['smtp_security'] = "force_tls"
            else:
                config['smtp_security'] = "off"

            config['smtp_username'] = step_input("SMTP Username: ").strip()
            config['smtp_password'] = step_input("SMTP Password: ").strip()
            config['smtp_from'] = step_input("From Email: ").strip()
        else:
            show_step_detail("Email not configured. Password recovery will be disabled.")

        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install Vaultwarden using Docker Compose'''

        instance_name = config.get('instance_name', 'vaultwarden')
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
                # Filter out Docker pull progress, show only actual errors
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

        instance_name = config.get('instance_name', 'vaultwarden')
        volume_name = config.get('volume_name', 'vaultwarden_data')

        # Build domain URL
        server_host = config.get('server_host', 'localhost')
        port = config.get('port', 8080)
        domain_url = f"http://{server_host}:{port}"

        compose_lines = [
            "services:",
            f"  {instance_name}:",
            "    image: vaultwarden/server:latest",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {port}:80",
            "    environment:",
            f"      - DOMAIN={domain_url}",
            f"      - SIGNUPS_ALLOWED={config.get('signups_allowed', 'false')}",
            "      - INVITATIONS_ALLOWED=true",
            "      - SHOW_PASSWORD_HINT=false",
            "      - WEB_VAULT_ENABLED=true"
        ]

        # Admin token
        if config.get('admin_token'):
            compose_lines.append(f"      - ADMIN_TOKEN={config['admin_token']}")

        # SMTP configuration
        if config.get('smtp_host'):
            compose_lines.extend([
                f"      - SMTP_HOST={config['smtp_host']}",
                f"      - SMTP_PORT={config['smtp_port']}",
                f"      - SMTP_SECURITY={config.get('smtp_security', 'starttls')}",
                f"      - SMTP_USERNAME={config['smtp_username']}",
                f"      - SMTP_PASSWORD={config['smtp_password']}",
                f"      - SMTP_FROM={config['smtp_from']}"
            ])

        # Volumes
        compose_lines.extend([
            "    volumes:",
            f"      - {volume_name}:/data",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ])

        return '\n'.join(compose_lines)
