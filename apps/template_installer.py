import json
import os
import re
import secrets
from apps.installer_base import BaseInstaller
from utils.docker_progress import run_docker_with_progress
from utils.validation import sanitize_yaml_value, validate_container_name


def _parse_docker_error(stderr):
    """Parse Docker stderr into a short, readable error message."""
    text = stderr.strip()
    if not text:
        return ''
    lower = text.lower()

    if 'port is already allocated' in lower:
        m = re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)', text)
        port = m.group(1) if m else 'unknown'
        return f'Port {port} is already in use. Choose a different port.'

    if 'is the docker daemon running' in lower or 'cannot connect' in lower:
        return 'Docker is not running. Start Docker first.'

    if 'no such image' in lower or 'manifest unknown' in lower:
        return 'Docker image not found. Check your internet connection.'

    if 'network' in lower and 'not found' in lower:
        return 'Docker network error. Try restarting Docker.'

    if 'permission denied' in lower:
        return 'Permission denied. Run with admin/sudo privileges.'

    if 'no space left' in lower:
        return 'No disk space left. Free up space and try again.'

    # Fallback: extract last meaningful line
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line and not line.startswith(('time=', ' ', '|')):
            return line[:200] if len(line) > 200 else line

    return 'Unknown error. Check Docker logs for details.'


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
            self._cleanup_failed(instance_name)
            self._last_error = _parse_docker_error(result.stderr or '')
            return False

        # Clean up anonymous volumes after successful install
        self._cleanup_anon_volumes(instance_name)
        return True

    def get_last_error(self):
        """Return the last install error message."""
        return getattr(self, '_last_error', '')

    def _cleanup_failed(self, instance_name):
        """Remove container and orphan volumes after failed install."""
        from utils.docker_utils import safe_docker_run

        # Get anonymous volumes before removing container
        result = safe_docker_run(
            ['docker', 'inspect', instance_name, '--format', '{{json .Mounts}}'],
            capture_output=True, text=True
        )
        anon_vols = []
        if result and result.returncode == 0:
            try:
                for m in json.loads(result.stdout.strip()):
                    name = m.get('Name', '')
                    if (m.get('Type') == 'volume' and len(name) == 64
                            and all(c in '0123456789abcdef' for c in name)):
                        anon_vols.append(name)
            except (json.JSONDecodeError, ValueError):
                pass

        # Remove failed container
        safe_docker_run(
            ['docker', 'rm', '-f', instance_name],
            capture_output=True, text=True
        )

        # Remove anonymous volumes
        for vol in anon_vols:
            safe_docker_run(
                ['docker', 'volume', 'rm', '-f', vol],
                capture_output=True, text=True
            )

        # Remove named volumes we created
        for v in self.template.get('volumes', []):
            if not v.get('bind'):
                vol_name = f"{instance_name}_{v['name_suffix']}"
                safe_docker_run(
                    ['docker', 'volume', 'rm', '-f', vol_name],
                    capture_output=True, text=True
                )

    def _cleanup_anon_volumes(self, instance_name):
        """Map image VOLUME paths to named volumes to prevent anonymous volumes."""
        from utils.docker_utils import safe_docker_run

        # Inspect container mounts to find anonymous volumes and their paths
        result = safe_docker_run(
            ['docker', 'inspect', instance_name, '--format', '{{json .Mounts}}'],
            capture_output=True, text=True
        )
        if not result or result.returncode != 0:
            return

        try:
            mounts = json.loads(result.stdout.strip())
        except (json.JSONDecodeError, ValueError):
            return

        anon_mounts = []
        for m in mounts:
            name = m.get('Name', '')
            if (m.get('Type') == 'volume' and len(name) == 64
                    and all(c in '0123456789abcdef' for c in name)):
                anon_mounts.append({'name': name, 'dest': m['Destination']})

        if not anon_mounts:
            return

        compose_file = f"docker-compose-{instance_name}.yml"

        # Add named volumes for each anonymous mount path in compose
        with open(compose_file, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        # Find last service-level volume line (indented "      - ...")
        last_svc_vol = -1
        for i, line in enumerate(lines):
            if re.match(r'^      - \S+:/', line):
                last_svc_vol = i

        new_vol_lines = []
        new_vol_defs = []
        for m in anon_mounts:
            suffix = m['dest'].strip('/').replace('/', '_').replace('.', '_')
            vol_name = f"{instance_name}_{suffix}"
            new_vol_lines.append(f"      - {vol_name}:{m['dest']}")
            new_vol_defs.append(f"  {vol_name}:\n    name: {vol_name}")

        # Insert volume mappings after last service volume line
        if last_svc_vol >= 0:
            for j, vl in enumerate(new_vol_lines):
                lines.insert(last_svc_vol + 1 + j, vl)

        # Add volume definitions at end
        for vd in new_vol_defs:
            lines.append(vd)

        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        # Recreate: down removes container + anon volumes, up uses updated compose
        safe_docker_run(
            ['docker', 'compose', '-f', compose_file, 'down'],
            capture_output=True, text=True
        )
        for m in anon_mounts:
            safe_docker_run(
                ['docker', 'volume', 'rm', '-f', m['name']],
                capture_output=True, text=True
            )
        safe_docker_run(
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            capture_output=True, text=True
        )

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
