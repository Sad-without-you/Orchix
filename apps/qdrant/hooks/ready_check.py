# ORCHIX v1.1
'''Ready check hook for Qdrant'''

import subprocess
import time
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 30) -> bool:
    '''Wait for Qdrant to be ready'''
    show_info(f"  Waiting for Qdrant to be ready...")

    for i in range(timeout):
        result = subprocess.run(
            ['docker', 'exec', container_name, 'wget', '-q', '--spider', 'http://localhost:6333/'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0:
            show_success(f"  ✓ Qdrant ready!")
            return True

        time.sleep(1)

    show_warning(f"  ⚠ Qdrant not ready after {timeout}s")
    return False
