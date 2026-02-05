from apps.installer_base import BaseInstaller


class NginxInstaller(BaseInstaller):
    '''Installer for Nginx Proxy Manager'''
    
    def get_default_config(self):
        '''Get default configuration'''
        return {
            'image': 'jc21/nginx-proxy-manager:latest',
            'http_port': 8080,
            'https_port': 8443,
            'admin_port': 8081
        }
    
    def check_dependencies(self):
        '''Check if all dependencies are met'''
        return True
    
    def get_configuration(self, instance_name=None):
        '''Get configuration from user'''
        from cli.ui import show_step_detail, show_step_line, step_input

        config = self.get_default_config()

        show_step_line()
        show_step_detail("Nginx Proxy Manager Configuration")
        show_step_line()
        show_step_detail("Nginx Proxy Manager provides:")
        show_step_detail("Web UI for managing reverse proxies")
        show_step_detail("Automatic Let's Encrypt SSL certificates")
        show_step_detail("Access control and authentication")
        show_step_detail("Easy domain management")
        show_step_line()

        # HTTP Port
        http_input = step_input(f"HTTP port [{config['http_port']}]: ").strip()
        if http_input:
            config['http_port'] = int(http_input)

        # HTTPS Port
        https_input = step_input(f"HTTPS port [{config['https_port']}]: ").strip()
        if https_input:
            config['https_port'] = int(https_input)

        # Admin Port
        admin_input = step_input(f"Admin UI port [{config['admin_port']}]: ").strip()
        if admin_input:
            config['admin_port'] = int(admin_input)

        show_step_line()
        show_step_detail("Default admin credentials:")
        show_step_detail("Email:    admin@example.com")
        show_step_detail("Password: changeme")
        show_step_detail("CHANGE THESE IMMEDIATELY AFTER LOGIN!")
        show_step_line()

        step_input("Press Enter to continue...")
        
        return config
    
    def generate_compose(self, instance_name, config):
        '''Generate docker-compose.yml'''
        
        compose = {
            'version': '3.8',
            'services': {
                instance_name: {
                    'image': config['image'],
                    'container_name': instance_name,
                    'restart': 'unless-stopped',
                    'ports': [
                        f"{config['http_port']}:80",      # HTTP
                        f"{config['admin_port']}:81",     # Admin UI
                        f"{config['https_port']}:443"     # HTTPS
                    ],
                    'volumes': [
                        f"{instance_name}_data:/data",
                        f"{instance_name}_letsencrypt:/etc/letsencrypt"
                    ],
                    'environment': [
                        'DISABLE_IPV6=true'
                    ]
                }
            },
            'volumes': {
                f'{instance_name}_data': {},
                f'{instance_name}_letsencrypt': {}
            }
        }
        
        return compose
    
    def install(self, config, instance_name=None):
        '''Install Nginx Proxy Manager'''
        import subprocess
        from pathlib import Path
        import yaml
        from cli.ui import show_step_detail
        from utils.docker_progress import run_docker_with_progress, filter_docker_errors

        if not instance_name:
            instance_name = config.get('instance_name', 'nginx')

        # Generate compose
        compose_content = self.generate_compose(instance_name, config)
        compose_file = Path(f'docker-compose-{instance_name}.yml')

        show_step_detail("Creating Docker Compose file...")
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f, default_flow_style=False, sort_keys=False)

        # Pull image
        result = run_docker_with_progress(
            ['docker', 'pull', config['image']],
            f"Pulling {config['image']}",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            show_step_detail(f"Failed to pull image: {result.stderr}")
            return False

        # Start container
        result = run_docker_with_progress(
            ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
            f"Starting {instance_name} container",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            show_step_detail(f"Failed to start: {result.stderr}")
            return False

        return True