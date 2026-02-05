# ORCHIX v1.1
'''Success message hook for Stirling PDF'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 8080)
    
    message = f"""📄 Stirling PDF installed successfully!

Stirling PDF Web Interface:
  http://localhost:{port}

Features:
  • PDF merging and splitting
  • Image conversion
  • PDF compression
  • Watermarking
  • OCR support
  • And many more tools!

Access:
  Open http://localhost:{port} in your browser to get started.
"""
    
    return message
