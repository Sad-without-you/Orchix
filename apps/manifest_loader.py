# ORCHIX v1.3 - Template-only manifest loader
import json
from pathlib import Path


def _load_templates():
    '''Load all apps from templates.json and build synthetic manifests.'''
    templates_file = Path('apps') / 'templates.json'
    if not templates_file.exists():
        return {}

    try:
        with open(templates_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    manifests = {}
    for t in data.get('templates', []):
        name = t.get('name')
        if not name:
            continue

        manifest = {
            'name': name,
            'display_name': t.get('display_name', name),
            'description': t.get('description', ''),
            'icon': t.get('icon', ''),
            'version': t.get('version', 'latest'),
            'license_required': t.get('license_required'),
            'requires': {'system': ['docker'], 'containers': []},
            'default_ports': [p['default_host'] for p in t.get('ports', [])],
            'volumes': [
                f"{name}_{v['name_suffix']}" for v in t.get('volumes', [])
                if v.get('name_suffix')
            ],
            'networks': [],
            'hooks': {},
            'image_size_mb': t.get('image_size_mb', 0),
            '_template': t,
            '_is_template': True,
        }

        manifest['installer_class'] = _make_installer_class(t)
        manifest['updater_class'] = _make_updater_class(t)

        manifests[name] = manifest

    return manifests


def _make_installer_class(template):
    """Return a class that creates a TemplateInstaller with template data."""
    from apps.template_installer import TemplateInstaller

    class BoundTemplateInstaller(TemplateInstaller):
        def __init__(self, manifest):
            super().__init__(manifest, template)

    return BoundTemplateInstaller


def _make_updater_class(template):
    """Return a class that creates a TemplateUpdater with template data."""
    from apps.template_updater import TemplateUpdater

    class BoundTemplateUpdater(TemplateUpdater):
        def __init__(self, manifest):
            super().__init__(manifest, template)

    return BoundTemplateUpdater


def load_manifest(app_name):
    '''Load a single app manifest by name.'''
    templates = _load_templates()
    if app_name in templates:
        return templates[app_name]
    raise ValueError(f"App '{app_name}' not found")


def load_all_manifests():
    '''Load manifests for all template apps.'''
    try:
        return _load_templates()
    except Exception as e:
        print(f"Warning: Could not load templates: {e}")
        return {}
