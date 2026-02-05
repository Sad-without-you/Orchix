# ORCHIX v1.1
'''Success message hook for Redis'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 6379)
    password = config.get('password')
    
    message = f"""🔴 Redis installed successfully!

Redis Connection:
  Host: localhost
  Port: {port}
"""
    
    if password:
        message += f"  Password: {password}\n"
        message += f"  CLI: redis-cli -h localhost -p {port} -a {password}\n"
    else:
        message += f"  CLI: redis-cli -h localhost -p {port}\n"
    
    return message