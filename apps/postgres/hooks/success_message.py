# ORCHIX v1.1
'''Success message hook for PostgreSQL'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 5432)
    database = config.get('database', 'postgres')
    user = config.get('user', 'postgres')
    password = config.get('password', '(see compose file)')
    
    message = f"""🐘 PostgreSQL installed successfully!

Database Connection:
  Host: localhost
  Port: {port}
  Database: {database}
  User: {user}
  Password: {password}
"""
    
    return message