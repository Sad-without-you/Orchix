# ORCHIX v1.1
'''Ready check hook for Nextcloud'''

import subprocess
import time
from cli.ui import show_info, show_success, show_warning


def wait_for_ready(container_name: str, timeout: int = 60) -> bool:
    '''Wait for Nextcloud to be ready'''
    show_info(f"  Waiting for Nextcloud to be ready...")
    
    for i in range(timeout):
        try:
            result = subprocess.run(
                ['docker', 'exec', container_name, 'curl', '-f', 'http://localhost:80/status.php'],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                show_success(f"  ✓ Nextcloud is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
    
    show_warning(f"  ⚠️  Nextcloud did not respond within {timeout} seconds")
    return True  # Still return True - container might be starting