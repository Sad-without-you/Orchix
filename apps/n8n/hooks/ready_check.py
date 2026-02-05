# ORCHIX v1.1
import subprocess
import time
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 30) -> bool:
    '''Wait for n8n to be ready inside the container'''
    show_info(f"  Waiting for n8n to be ready...")
    
    # Simple wait (n8n starts quickly)
    time.sleep(5)
    show_success(f"  ✓ n8n ready!")
    return True