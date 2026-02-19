import json
import subprocess
from utils.docker_utils import ORCHIX_NETWORK

# Maps db_type → (image keywords, exposed ports)
# Both methods are used: image name is fast and reliable,
# port check catches any DB that doesn't match known image names
_DB_TYPES = {
    'mysql':    {'images': ['mariadb', 'mysql', 'percona'],  'ports': {3306}},
    'postgres': {'images': ['postgres', 'postgresql'],        'ports': {5432}},
    'redis':    {'images': ['redis'],                         'ports': {6379}},
    'mongo':    {'images': ['mongo'],                         'ports': {27017}},
    'influxdb': {'images': ['influxdb'],                      'ports': {8086}},
}

# Maps image keyword → env var names for credential extraction
_CREDENTIAL_ENV_MAP = {
    'mariadb': {'user': 'MARIADB_USER', 'password': 'MARIADB_PASSWORD', 'database': 'MARIADB_DATABASE'},
    'mysql':   {'user': 'MYSQL_USER',   'password': 'MYSQL_PASSWORD',   'database': 'MYSQL_DATABASE'},
    'postgres':{'user': 'POSTGRES_USER','password': 'POSTGRES_PASSWORD','database': 'POSTGRES_DB'},
    'mongo':   {'user': 'MONGO_INITDB_ROOT_USERNAME', 'password': 'MONGO_INITDB_ROOT_PASSWORD', 'database': 'MONGO_INITDB_DATABASE'},
}


def _get_container_info(container_name):
    """Return (image_lower, exposed_ports_set) for a container."""
    result = subprocess.run(
        ['docker', 'inspect', container_name,
         '--format', '{{.Config.Image}}\t{{json .Config.ExposedPorts}}'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return '', set()

    parts = result.stdout.strip().split('\t', 1)
    image = parts[0].lower() if parts else ''

    ports = set()
    if len(parts) > 1:
        try:
            exposed = json.loads(parts[1]) or {}
            ports = {int(p.split('/')[0]) for p in (exposed.keys() if exposed else [])}
        except Exception:
            pass

    return image, ports


def _matches_db_type(image, ports, type_def):
    """Check if a container matches a db type by image name OR by port."""
    if any(kw in image for kw in type_def['images']):
        return True
    if ports and ports.intersection(type_def['ports']):
        return True
    return False


def discover_db_containers(db_types=None):
    """
    Return running ORCHIX containers that look like database servers.
    Uses image-name (primary) and exposed port (fallback) for detection.

    db_types: optional list of type names (e.g. ['mysql']) to restrict results.
              If None, all DB types are returned.
    Each entry: {'name': str, 'image': str}
    """
    if db_types:
        type_defs = {t: _DB_TYPES[t] for t in db_types if t in _DB_TYPES}
    else:
        type_defs = _DB_TYPES

    try:
        net_result = subprocess.run(
            ['docker', 'network', 'inspect', ORCHIX_NETWORK,
             '--format', '{{range $k, $v := .Containers}}{{$v.Name}}\n{{end}}'],
            capture_output=True, text=True
        )
        if net_result.returncode != 0:
            return []

        candidates = []
        for name in net_result.stdout.strip().splitlines():
            name = name.strip()
            if not name:
                continue

            image, ports = _get_container_info(name)

            if any(_matches_db_type(image, ports, td) for td in type_defs.values()):
                candidates.append({'name': name, 'image': image or name})

        return candidates

    except Exception:
        return []


def get_db_credentials(container_name):
    """
    Read user/password/database credentials from a DB container's compose file.
    Returns dict with keys 'user', 'password', 'database' (whichever are available).
    """
    from pathlib import Path

    compose_file = Path(f'docker-compose-{container_name}.yml')
    if not compose_file.exists():
        return {}

    try:
        content = compose_file.read_text(encoding='utf-8')
    except OSError:
        return {}

    # Parse env vars from compose YAML lines (format: "      - KEY=value")
    env_vars = {}
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('- ') and '=' in stripped:
            key, _, val = stripped[2:].partition('=')
            env_vars[key.strip()] = val.strip()

    # Get image to select the right credential map
    img_result = subprocess.run(
        ['docker', 'inspect', container_name, '--format', '{{.Config.Image}}'],
        capture_output=True, text=True
    )
    image = img_result.stdout.strip().lower() if img_result.returncode == 0 else ''

    for img_kw, mapping in _CREDENTIAL_ENV_MAP.items():
        if img_kw in image or any(k in env_vars for k in mapping.values()):
            creds = {role: env_vars[env_key]
                     for role, env_key in mapping.items()
                     if env_key in env_vars}
            if creds:
                return creds

    return {}
