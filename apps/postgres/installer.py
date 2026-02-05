from apps.installer_base import BaseInstaller
import subprocess
import secrets
import os
from cli.ui import show_step_detail, show_step_line, step_input
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class PostgresInstaller(BaseInstaller):
    '''Installer for PostgreSQL database'''
    
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
        '''Get PostgreSQL configuration from user'''
    
        show_step_detail("Configure PostgreSQL database")
        show_step_line()

        config = {}

        # Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]

        # Database name
        default_db = 'postgres'
        db_name = step_input(f"Database name (default: {default_db}): ").strip()
        config['database'] = db_name if db_name else default_db

        # Username
        default_user = 'postgres'
        username = step_input(f"Username (default: {default_user}): ").strip()
        config['user'] = username if username else default_user
        
        # Password - Rich UI Selection
        from cli.ui import step_select
        
        pwd_choice = step_select(
            "Password generation",
            [
                "🔐 Auto-generate (recommended)",
                "✏️  Enter custom password"
            ]
        )
        
        if "custom" in pwd_choice:
            password = step_input("Enter password: ").strip()
            if password:
                config['password'] = password
            else:
                show_step_detail("Empty password, auto-generating...")
                config['password'] = secrets.token_urlsafe(16)
        else:
            config['password'] = secrets.token_urlsafe(16)
        
        # PostgreSQL Version - Rich UI Selection
        version_choice = step_select(
            "PostgreSQL Version",
            [
                "16 (Latest)",
                "15",
                "14",
                "13"
            ]
        )
        
        # Extract version number
        config['version'] = version_choice.split()[0]  # "16 (Latest)" -> "16"
        
        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install PostgreSQL using Docker Compose'''
        
        instance_name = config.get('instance_name', 'postgres')
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
        
        instance_name = config.get('instance_name', 'postgres')
        volume_name = config.get('volume_name', 'postgres_data')
        version = config.get('version', '16')
        
        compose_lines = [
            "services:",
            f"  {instance_name}:",
            f"    image: postgres:{version}",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:5432",
            "    environment:",
            f"      - POSTGRES_DB={config.get('database', 'postgres')}",
            f"      - POSTGRES_USER={config.get('user', 'postgres')}",
            f"      - POSTGRES_PASSWORD={config['password']}",
            "    volumes:",
            f"      - {volume_name}:/var/lib/postgresql/data",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ]
        
        return '\n'.join(compose_lines)