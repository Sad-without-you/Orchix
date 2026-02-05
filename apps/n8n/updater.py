from apps.updater_base import BaseUpdater
import subprocess
import os
from cli.ui import show_success, show_warning, show_error, show_step_detail, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors 
            
class N8nUpdater(BaseUpdater):
    '''Updater for n8n workflow automation'''
    
    def get_available_actions(self):
        '''n8n supports multiple update types'''
        return ['config_update', 'beta_update', 'next_update', 'version_update']
    
    def quick_update(self):
        '''Quick update - restart container'''
        try:
            container_name = self.app_name
            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            show_step_detail(f"Quick update failed: {e}")
            return False
    
    def config_update(self):
        '''Update configuration and recreate container'''
        try:
            
            container_name = self.app_name
            compose_file = self._find_compose_file(container_name)
            
            if not compose_file:
                show_step_detail(f"Compose file not found for {container_name}")
                return False
            
            show_step_detail("Updating configuration...")
            
            # Read CURRENT compose file
            with open(compose_file, 'r', encoding='utf-8') as f:
                current_compose = f.read()
            
            # Extract CURRENT settings
            import re
            
            # Encryption Key (MUST preserve!)
            current_key_match = re.search(r'N8N_ENCRYPTION_KEY=([a-f0-9]+)', current_compose)
            encryption_key = current_key_match.group(1) if current_key_match else None
            
            if not encryption_key:
                show_error("Could not find current encryption key!")
                return False
            
            show_step_detail(f"Using existing encryption key: {encryption_key[:16]}...")
            
            # Current port
            result = subprocess.run(
                ['docker', 'port', container_name, '5678'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0 and result.stdout:
                current_port = int(result.stdout.strip().split(':')[-1])
            else:
                current_port = 5678
            
            show_step_detail(f"Current port: {current_port}")

            # Ask for NEW configuration (only changeable settings)
            show_step_detail("Enter new configuration (press Enter to keep current):")

            # Port
            new_port = step_input(f"Port (current: {current_port}): ").strip()
            if new_port:
                try:
                    port = int(new_port)
                except ValueError:
                    show_warning(f"Invalid port, keeping current: {current_port}")
                    port = current_port
            else:
                port = current_port
            
            # Timezone
            current_tz_match = re.search(r'GENERIC_TIMEZONE=([^\n]+)', current_compose)
            current_tz = current_tz_match.group(1).strip() if current_tz_match else 'Europe/Berlin'
            
            new_tz = step_input(f"Timezone (current: {current_tz}): ").strip()
            timezone = new_tz if new_tz else current_tz
            
            # Host
            current_host_match = re.search(r'N8N_HOST=([^\n]+)', current_compose)
            current_host = current_host_match.group(1).strip() if current_host_match else '0.0.0.0'
            
            new_host = step_input(f"Host (current: {current_host}): ").strip()
            host = new_host if new_host else current_host
            
            # Protocol
            current_proto_match = re.search(r'N8N_PROTOCOL=([^\n]+)', current_compose)
            current_proto = current_proto_match.group(1).strip() if current_proto_match else 'http'
            
            proto_choice = step_select(
                f"Protocol (current: {current_proto})",
                [
                    "🔓 http",
                    "🔒 https"
                ]
            )
            protocol = 'https' if 'https' in proto_choice else 'http'
            
            # Webhook URL
            current_webhook_match = re.search(r'WEBHOOK_URL=([^\n]+)', current_compose)
            current_webhook = current_webhook_match.group(1).strip() if current_webhook_match else ''
            
            webhook_display = current_webhook if current_webhook else '(not set)'
            new_webhook = step_input(f"Webhook URL (current: {webhook_display}): ").strip()
            webhook_url = new_webhook if new_webhook else current_webhook
            
            # Basic Auth
            has_auth = 'N8N_BASIC_AUTH_ACTIVE=true' in current_compose
            
            enable_auth = step_select(
                f"Basic Authentication (current: {'Enabled' if has_auth else 'Disabled'})",
                [
                    "❌ Disabled",
                    "✅ Enabled"
                ]
            )
            
            basic_auth_user = None
            basic_auth_password = None
            
            if "Enabled" in enable_auth:
                if has_auth:
                    current_user_match = re.search(r'N8N_BASIC_AUTH_USER=([^\n]+)', current_compose)
                    current_user = current_user_match.group(1).strip() if current_user_match else ''
                    
                    new_user = step_input(f"Username (current: {current_user}): ").strip()
                    basic_auth_user = new_user if new_user else current_user
                    
                    new_password = step_input("Password (leave empty to keep current): ").strip()
                    if new_password:
                        basic_auth_password = new_password
                    else:
                        # Keep current password
                        current_pass_match = re.search(r'N8N_BASIC_AUTH_PASSWORD=([^\n]+)', current_compose)
                        basic_auth_password = current_pass_match.group(1).strip() if current_pass_match else ''
                else:
                    basic_auth_user = step_input("Username: ").strip()
                    basic_auth_password = step_input("Password: ").strip()
            
            # Build new config
            config = {
                'port': port,
                'encryption_key': encryption_key,
                'timezone': timezone,
                'host': host,
                'protocol': protocol,
                'instance_name': container_name,
                'volume_name': f"{container_name}_data"
            }
            
            if webhook_url:
                config['webhook_url'] = webhook_url
            
            if basic_auth_user and basic_auth_password:
                config['basic_auth_user'] = basic_auth_user
                config['basic_auth_password'] = basic_auth_password
            
            show_success("Configuration ready!")
            
            # Force reload installer module (avoid cache issues)
            import sys
            if 'apps.n8n.installer' in sys.modules:
                del sys.modules['apps.n8n.installer']
            
            # Generate new compose
            from apps.n8n.installer import N8nInstaller
            installer = N8nInstaller(self.manifest)
            new_compose = installer._generate_compose(config)
            
            # Write new compose
            with open(compose_file, 'w', encoding='utf-8') as f:
                f.write(new_compose)
            
            show_success("Compose file updated!")
            
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
                "Starting container with new configuration",
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                show_error("Failed to start container!")
                show_step_detail(f"Error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            show_step_detail(f"Config update failed: {e}")
            return False

    def beta_update(self):
        '''Update to beta version'''
        return self._update_to_tag('beta')
    
    def next_update(self):
        '''Update to next version'''
        return self._update_to_tag('next')
    
    def version_update(self):
        '''Update to latest stable version'''
        return self._update_to_tag('latest')
    
    def _update_to_tag(self, tag):
        '''Update to specific image tag'''
        try:
            container_name = self.app_name
            compose_file = self._find_compose_file(container_name)
            
            # Pull image
            result = run_docker_with_progress(
                ['docker', 'pull', f'n8nio/n8n:{tag}'],
                f"Pulling n8nio/n8n:{tag}",
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                show_step_detail(f"Pull failed: {result.stderr}")
                return False
            
            # Update compose file if exists
            if compose_file:
                # Read current compose
                with open(compose_file, 'r', encoding='utf-8') as f:
                    compose_content = f.read()
                
                # Replace image tag
                compose_content = compose_content.replace(
                    'image: n8nio/n8n:latest',
                    f'image: n8nio/n8n:{tag}'
                ).replace(
                    'image: n8nio/n8n:beta',
                    f'image: n8nio/n8n:{tag}'
                ).replace(
                    'image: n8nio/n8n:next',
                    f'image: n8nio/n8n:{tag}'
                )
                
                # Write updated compose
                with open(compose_file, 'w', encoding='utf-8') as f:
                    f.write(compose_content)
                
                # Stop and remove old container
                show_step_detail("Stopping old container...")
                subprocess.run(
                    ['docker', 'compose', '-f', compose_file, 'down'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                # Force remove container if still exists
                show_step_detail("Ensuring old container is removed...")
                subprocess.run(
                    ['docker', 'rm', '-f', container_name],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                # Create with new image
                result = run_docker_with_progress(
                    ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                    "Starting container with new version",
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                # Fallback: direct docker commands
                show_step_detail("Stopping and removing container...")
                subprocess.run(
                    ['docker', 'rm', '-f', container_name],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                show_step_detail("Creating new container...")
                result = subprocess.run(
                    ['docker', 'run', '-d', '--name', container_name, f'n8nio/n8n:{tag}'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            
            if result.returncode != 0:
                show_step_detail(f"Command failed: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            show_step_detail(f"Update to {tag} failed: {e}")
            return False
        
    def _find_compose_file(self, container_name):
        '''Find compose file for container'''
        # Try different possible names
        possible_files = [
            f'docker-compose-{container_name}.yml',
            'docker-compose.yml',
            f'{container_name}-docker-compose.yml'
        ]
        
        for filepath in possible_files:
            if os.path.exists(filepath):
                return filepath
        
        return None