# ORCHIX v1.1
'''Ready check hook for Nginx Proxy Manager'''

import subprocess
import time
import socket
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 60) -> bool:
    '''Wait for Nginx Proxy Manager to be ready'''
    show_info(f"  Waiting for Nginx Proxy Manager to be ready (this may take a minute)...")
    
    # Get admin port from container (port 81)
    result = subprocess.run(
        ['docker', 'port', container_name, '81'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        show_warning(f"  ⚠ Could not get port mapping")
        time.sleep(5)
        return True
    
    # Extract port
    try:
        port_mapping = result.stdout.strip()
        # Format: 0.0.0.0:81
        port = int(port_mapping.split(':')[-1])
    except:
        port = 81
    
    # Check if port is responding
    for i in range(timeout):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                show_success(f"  ✓ Nginx Proxy Manager ready on port {port}!")
                return True
        except:
            pass
        
        time.sleep(1)
    
    show_warning(f"  ⚠ Nginx Proxy Manager not ready after {timeout}s (may still be initializing)")
    return False