# ORCHIX v1.1
def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 8085)
    
    message = f"""☁️ Nextcloud installed successfully!

Nextcloud Cloud Storage:
  http://localhost:{port}

Setup:
  1. Open http://localhost:{port} in your browser
  2. Create an admin account
  3. Choose database (SQLite pre-configured)
  4. Click "Install"
  5. Install recommended apps from app store

Features:
  • Cloud file storage
  • File sharing and collaboration
  • Calendar and contacts sync
  • Office document editing
  • Mobile apps available
"""
    
    return message