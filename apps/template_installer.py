import os
import secrets
from apps.installer_base import BaseInstaller
from utils.docker_progress import run_docker_with_progress
from utils.validation import sanitize_yaml_value, validate_container_name


class TemplateInstaller(BaseInstaller):
    """Generic installer for JSON-template-defined apps."""

    def __init__(self, manifest, template):
        super().__init__(manifest)
        self.template = template

    def check_dependencies(self):
        return True

    def get_configuration(self, instance_name=None):
        """CLI: Interactive prompts for each env variable."""
        from cli.ui import show_step_detail, show_step_line, step_input

        config = {}
        envs = self.template.get('env', [])

        if envs:
            show_step_line()
            show_step_detail(f"Configure {self.template['display_name']}")
            show_step_line()

        for env in envs:
            if env.get('generate'):
                val = secrets.token_urlsafe(16)
                show_step_detail(f"{env['label']}: [auto-generated]")
                config[env['key']] = val
            elif env.get('type') == 'select':
                options = env.get('options', [])
                default = env.get('default', options[0] if options else '')
                prompt = f"{env['label']} ({'/'.join(options)}) [{default}]: "
                val = step_input(prompt).strip()
                config[env['key']] = val if val in options else default
            else:
                default = env.get('default', '')
                val = step_input(f"{env['label']} [{default}]: ").strip()
                config[env['key']] = val or default

        # Port: use first port as default
        ports = self.template.get('ports', [])
        if ports:
            config['port'] = ports[0]['default_host']

        return config

    def get_web_configuration(self, user_config):
        """Web UI: Build config from request body, auto-generate passwords."""
        config = {}
        for env in self.template.get('env', []):
            if env.get('generate'):
                config[env['key']] = secrets.token_urlsafe(16)
            else:
                config[env['key']] = user_config.get(env['key'], env.get('default', ''))
        return config

    def install(self, config, instance_name=None):
        instance_name = config.get('instance_name', self.template['name'])
        # Validate instance name to prevent path traversal
        instance_name = validate_container_name(instance_name)
        compose = self._generate_compose(instance_name, config)
        compose_file = f"docker-compose-{instance_name}.yml"

        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(compose)

        result = run_docker_with_progress(
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            f"Pulling and starting {instance_name}",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            try:
                os.remove(compose_file)
            except OSError:
                pass
            return False
        return True

    def _generate_compose(self, instance_name, config):
        t = self.template
        port = config.get('port', t['ports'][0]['default_host'] if t.get('ports') else 8080)

        # Ports
        ports_lines = []
        for i, p in enumerate(t.get('ports', [])):
            host = port if i == 0 else p['default_host']
            proto = p.get('protocol', 'tcp')
            if proto == 'tcp/udp':
                ports_lines.append(f'      - "{host}:{p["container"]}/tcp"')
                ports_lines.append(f'      - "{host}:{p["container"]}/udp"')
            else:
                ports_lines.append(f'      - "{host}:{p["container"]}"')

        # Volumes (named volumes + bind mounts)
        vol_lines = []
        vol_defs = []
        for v in t.get('volumes', []):
            if v.get('bind'):
                # Bind mount: host path -> container path
                vol_lines.append(f"      - {v['bind']}:{v['mount']}")
            else:
                vol_name = f"{instance_name}_{v['name_suffix']}"
                vol_lines.append(f"      - {vol_name}:{v['mount']}")
                vol_defs.append(f"  {vol_name}:\n    name: {vol_name}")

        # Environment (sanitize values to prevent YAML injection)
        env_lines = []
        for e in t.get('env', []):
            val = str(config.get(e['key'], e.get('default', '')))
            safe_val = sanitize_yaml_value(val)
            env_lines.append(f"      - {e['key']}={safe_val}")

        # Build YAML
        sections = [f"services:\n  {instance_name}:"]
        sections.append(f"    image: {t['image']}")
        sections.append(f"    container_name: {instance_name}")
        sections.append(f"    restart: {t.get('restart', 'unless-stopped')}")

        if t.get('command'):
            sections.append(f"    command: {t['command']}")

        if ports_lines:
            sections.append("    ports:")
            sections.extend(ports_lines)

        if vol_lines:
            sections.append("    volumes:")
            sections.extend(vol_lines)

        if env_lines:
            sections.append("    environment:")
            sections.extend(env_lines)

        if vol_defs:
            sections.append("")
            sections.append("volumes:")
            sections.extend(vol_defs)

        return "\n".join(sections) + "\n"
