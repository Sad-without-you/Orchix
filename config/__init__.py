# ORCHIX v1.4
from pathlib import Path

# Central config directory for all ORCHIX data files
ORCHIX_CONFIG_DIR = Path.home() / 'orchix_configs'
ORCHIX_CONFIG_DIR.mkdir(exist_ok=True)
