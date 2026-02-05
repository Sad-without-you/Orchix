# ORCHIX v1.1
'''Ready check hook for LightRAG'''

import subprocess
import time
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 30) -> bool:
    '''Wait for LightRAG to be ready'''
    show_info(f"  Waiting for LightRAG to be ready...")

    for i in range(timeout):
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', container_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0 and 'true' in result.stdout.lower():
            show_success(f"  ✓ LightRAG ready!")
            return True

        time.sleep(1)

    show_warning(f"  ⚠ LightRAG not ready after {timeout}s")
    return False
