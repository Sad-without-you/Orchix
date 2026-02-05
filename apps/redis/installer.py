from apps.installer_base import BaseInstaller
import subprocess
import secrets
import os
from cli.ui import show_step_detail, show_step_line, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class RedisInstaller(BaseInstaller):
    '''Installer for Redis cache server'''
    
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
        '''Get Redis configuration from user'''
        
        show_step_detail("Configure Redis cache server")
        show_step_line()

        config = {}

        # Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]
        
        # Password
        pwd_choice = step_select(
            "Redis Password",
            [
                "🔐 Auto-generate (recommended)",
                "✏️  Enter custom password",
                "🔓 No password (insecure!)"
            ]
        )
        
        if "custom" in pwd_choice:
            password = step_input("Enter password: ").strip()
            config['password'] = password if password else secrets.token_urlsafe(16)
        elif "No password" in pwd_choice:
            config['password'] = None
        else:
            config['password'] = secrets.token_urlsafe(16)
        
        # Persistence
        persist_choice = step_select(
            "Data Persistence",
            [
                "💾 Enabled (RDB + AOF)",
                "⚡ Disabled (In-memory only)"
            ]
        )
        
        config['persistence'] = "Enabled" in persist_choice
        
        # Max Memory
        maxmem_choice = step_select(
            "Max Memory",
            [
                "256mb",
                "512mb",
                "1gb",
                "2gb",
                "✏️  Custom"
            ]
        )
        
        if "Custom" in maxmem_choice:
            custom_mem = step_input("Enter max memory (e.g., 512mb, 2gb): ").strip()
            config['maxmemory'] = custom_mem if custom_mem else "512mb"
        else:
            config['maxmemory'] = maxmem_choice
        
        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install Redis using Docker Compose'''
        
        instance_name = config.get('instance_name', 'redis')
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
        
        instance_name = config.get('instance_name', 'redis')
        volume_name = config.get('volume_name', 'redis_data')
        
        compose_lines = [
            "services:",
            f"  {instance_name}:",
            "    image: redis:7-alpine",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:6379"
        ]
        
        # Command with options
        cmd_parts = ["redis-server"]
        
        # Password
        if config.get('password'):
            cmd_parts.append(f"--requirepass {config['password']}")
        
        # Persistence
        if config.get('persistence'):
            cmd_parts.append("--appendonly yes")
            cmd_parts.append("--save 900 1")
            cmd_parts.append("--save 300 10")
            cmd_parts.append("--save 60 10000")
        
        # Max Memory
        if config.get('maxmemory'):
            cmd_parts.append(f"--maxmemory {config['maxmemory']}")
            cmd_parts.append("--maxmemory-policy allkeys-lru")
        
        if len(cmd_parts) > 1:
            compose_lines.append(f"    command: {' '.join(cmd_parts)}")
        
        # Volumes (only if persistence enabled)
        if config.get('persistence'):
            compose_lines.extend([
                "    volumes:",
                f"      - {volume_name}:/data"
            ])
        
        # Add volumes section if needed
        if config.get('persistence'):
            compose_lines.extend([
                "",
                "volumes:",
                f"  {volume_name}:",
                f"    name: {volume_name}"
            ])
        
        return '\n'.join(compose_lines)