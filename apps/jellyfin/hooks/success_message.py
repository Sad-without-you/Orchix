# ORCHIX v1.1
'''Success message hook for Jellyfin'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    http_port = config.get('http_port', 8096)
    https_port = config.get('https_port', 8920)
    
    message = f"""🎬 Jellyfin installed successfully!

Jellyfin Media Server:
  HTTP:  http://localhost:{http_port}
  HTTPS: https://localhost:{https_port}

Setup:
  1. Open http://localhost:{http_port} in your browser
  2. Follow the initial setup wizard
  3. Add your media libraries
  4. Start enjoying your media!
"""
    
    return message