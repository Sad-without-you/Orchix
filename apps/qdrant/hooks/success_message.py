# ORCHIX v1.1
'''Success message hook for Qdrant'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 6333)
    grpc_port = config.get('grpc_port', 6334)
    api_key = config.get('api_key')

    message = f"""🔍 Qdrant installed successfully!

Qdrant API Endpoints:
  HTTP API: http://localhost:{port}
  gRPC API: localhost:{grpc_port}
  Web UI: http://localhost:{port}/dashboard
"""

    if api_key:
        message += f"""
API Authentication:
  API Key: {api_key}
  Header: api-key: {api_key}
"""
    else:
        message += """
⚠ Warning: No API key configured (insecure!)
"""

    message += """
Next Steps:
  1. Open the Web UI in your browser
  2. Create your first collection
  3. Start indexing vectors
  4. Use the REST API or Python client
"""

    return message
