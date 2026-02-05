# ORCHIX v1.1
def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 8080)
    server_host = config.get('server_host', 'localhost')
    admin_token = config.get('admin_token')
    signups_allowed = config.get('signups_allowed', 'false')

    url = f"http://{server_host}:{port}"

    message = f"""🔐 Vaultwarden installed successfully!

Vaultwarden Web Vault:
  URL: {url}

Getting Started:
  1. Open {url} in your browser
  2. {"Create your account" if signups_allowed == "true" else "Use an invitation link to register"}
  3. Install Bitwarden browser extension or mobile app
  4. Point it to your server: {url}
  5. Login with your credentials

Compatible Clients:
  ✓ Bitwarden Browser Extension (Chrome, Firefox, Edge)
  ✓ Bitwarden Mobile Apps (iOS, Android)
  ✓ Bitwarden Desktop Apps (Windows, Mac, Linux)
  ✓ Bitwarden CLI

Configuration:
  Signups Allowed: {signups_allowed}
  Web Vault: Enabled
  Invitations: Enabled
"""

    if admin_token:
        message += f"""
Admin Panel:
  URL: {url}/admin
  Token: {admin_token}

  ⚠️  SAVE THE ADMIN TOKEN! You need it to access the admin panel.
"""
    else:
        message += """
Admin Panel: Disabled (no token configured)
"""

    if not config.get('smtp_host'):
        message += """
⚠️  Email not configured:
  - Password reset via email will not work
  - Configure SMTP in docker-compose if needed
"""

    message += """
Security Tips:
  - Use strong master password
  - Enable 2FA in account settings
  - Keep admin token secure
  - Regular backups of /data volume
  - Consider using HTTPS with reverse proxy
"""

    return message
