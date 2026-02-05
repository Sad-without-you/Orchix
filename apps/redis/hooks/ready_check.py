# ORCHIX v1.1
import subprocess
import time
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 10) -> bool:
    '''Wait for Redis to be ready'''
    show_info(f"  Waiting for Redis to be ready...")
    
    for i in range(timeout):
        result = subprocess.run(
            ['docker', 'exec', container_name, 'redis-cli', 'ping'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if 'PONG' in result.stdout:
            show_success(f"  ✓ Redis ready!")
            return True
        
        time.sleep(1)
    
    show_warning(f"  ⚠ Redis not ready after {timeout}s")
    return False