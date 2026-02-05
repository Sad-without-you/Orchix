# ORCHIX v1.1
def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 5678)
    
    message = f"""⚡ n8n installed successfully!

Web UI: http://localhost:{port}

Default credentials:
  Email: Create on first login
  Password: Create on first login
"""
    
    return message