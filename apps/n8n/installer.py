from readchar import config
from apps.installer_base import BaseInstaller
import secrets
from cli.ui import show_step_detail, show_step_line, step_input
from cli.ui import step_select
import subprocess
import secrets
import os
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class N8nInstaller(BaseInstaller):
    '''Installer for n8n workflow automation'''
    
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
        '''Get n8n configuration from user'''

        show_step_detail("Configure n8n environment variables")
        show_step_line()

        config = {}

        # Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]

        # Encryption Key - ALWAYS auto-generate (NO choice!)
        config['encryption_key'] = secrets.token_hex(32)
        show_step_detail(f"Generated encryption key: {config['encryption_key'][:16]}...")

        # Timezone
        default_tz = 'Europe/Berlin'
        timezone = step_input(f"Timezone (default: {default_tz}): ").strip()
        config['timezone'] = timezone if timezone else default_tz

        # Host
        default_host = '0.0.0.0'
        host = step_input(f"Host (default: {default_host}): ").strip()
        config['host'] = host if host else default_host
        
        # Protocol - Rich UI Selection
        protocol_choice = step_select(
            "Protocol",
            [
                "🔓 http (default)",
                "🔒 https"
            ]
        )
        
        config['protocol'] = 'https' if 'https' in protocol_choice else 'http'
        
        # Webhook URL (optional)
        webhook = step_input("Webhook URL (optional): ").strip()
        if webhook:
            config['webhook_url'] = webhook
        
        # Basic Auth - Rich UI Selection
        enable_auth = step_select(
            "Basic Authentication",
            [
                "❌ Disabled",
                "✅ Enabled"
            ]
        )
        
        if "Enabled" in enable_auth:
            config['basic_auth_user'] = step_input("Username: ").strip()
            config['basic_auth_password'] = step_input("Password: ").strip()

        show_step_line()
        show_step_detail("Configuration complete!")
        
        return config
    
    def install(self, config, instance_name=None):
        '''Install n8n using Docker Compose'''
        
        instance_name = config.get('instance_name', 'n8n')
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
            
            # Check result
            if result.returncode != 0:
                # Filter out Docker pull progress, show only actual errors
                error_output = filter_docker_errors(result.stderr)
                if error_output:
                    show_step_detail(f"Docker error: {error_output}")

                # CLEANUP: Remove compose file on failure
                try:
                    if os.path.exists(compose_file):
                        os.remove(compose_file)
                        show_step_detail(f"Cleaned up {compose_file}")
                except Exception as cleanup_error:
                    show_step_detail(f"Could not cleanup: {cleanup_error}")

                return False
            
            # Success!
            return True
            
        except Exception as e:
            show_step_detail(f"Installation failed: {e}")
            
            # CLEANUP: Remove compose file on exception
            try:
                if os.path.exists(compose_file):
                    os.remove(compose_file)
                    show_step_detail(f"Cleaned up {compose_file}")
            except Exception as cleanup_error:
                show_step_detail(f"Could not cleanup: {cleanup_error}")
            
            return False
    
    def _generate_compose(self, config):
        '''Generate docker-compose.yml content'''
        
        instance_name = config.get('instance_name', 'n8n')
        volume_name = config.get('volume_name', 'n8n_data')
        
        # Start with base compose
        protocol = config.get('protocol', 'http')
        secure_cookie = 'true' if protocol == 'https' else 'false'

        compose_lines = [
            "services:",
            f"  {instance_name}:",
            "    image: n8nio/n8n:latest",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:5678",
            "    environment:",
            "      - N8N_PORT=5678",
            f"      - N8N_PROTOCOL={protocol}",
            f"      - N8N_SECURE_COOKIE={secure_cookie}",
            f"      - N8N_ENCRYPTION_KEY={config['encryption_key']}",
            f"      - N8N_HOST={config.get('host', '0.0.0.0')}",
            f"      - GENERIC_TIMEZONE={config.get('timezone', 'Europe/Berlin')}"
        ]
        
        # Add optional environment variables
        if config.get('webhook_url'):
            compose_lines.append(f"      - WEBHOOK_URL={config['webhook_url']}")
        
        if config.get('basic_auth_user'):
            compose_lines.append("      - N8N_BASIC_AUTH_ACTIVE=true")
            compose_lines.append(f"      - N8N_BASIC_AUTH_USER={config['basic_auth_user']}")
            compose_lines.append(f"      - N8N_BASIC_AUTH_PASSWORD={config['basic_auth_password']}")
        
        # Add volumes
        compose_lines.extend([
            "    volumes:",
            f"      - {volume_name}:/home/node/.n8n",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ])
        
        # Join with newlines
        return '\n'.join(compose_lines)
