# ORCHIX v1.1
def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 3000)
    admin_user = config.get('admin_user', 'admin')
    admin_password = config.get('admin_password')

    message = f"""📊 Grafana installed successfully!

Grafana Web Interface:
  URL: http://localhost:{port}
  Username: {admin_user}
  Password: {admin_password}

Next Steps:
  1. Open Grafana in your browser
  2. Log in with the credentials above
  3. Add data sources (Prometheus, InfluxDB, etc.)
  4. Create dashboards or import from grafana.com
"""

    return message
