# ORCHIX v1.1
def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    http_port = config.get('http_port', 80)
    https_port = config.get('https_port', 443)
    admin_port = config.get('admin_port', 81)
    
    message = f"""🔒 Nginx Proxy Manager installed successfully!

Admin Interface:
   URL: http://localhost:{admin_port}
   
   Default Credentials:
   📧 Email:    admin@example.com
   🔑 Password: changeme
   
   ⚠️  IMPORTANT: Change these credentials immediately!

Proxy Ports:
   HTTP:  Port {http_port}
   HTTPS: Port {https_port}

Quick Start:
   1. Open admin UI: http://localhost:{admin_port}
   2. Login with default credentials
   3. Change email & password (Settings → Users)
   4. Add your first proxy host:
      • Hosts → Proxy Hosts → Add Proxy Host
      • Enter domain name
      • Enter target (e.g., http://n8n:5678)
      • Enable SSL with Let's Encrypt (1-click!)

Features:
   ✅ Automatic SSL certificates (Let's Encrypt)
   ✅ Automatic certificate renewal
   ✅ Reverse proxy management
   ✅ Access lists (password protection)
   ✅ Custom locations & redirections
   ✅ Stream (TCP/UDP) proxying

Documentation: https://nginxproxymanager.com/guide/

Common Use Cases:
   • Expose n8n with SSL: n8n.yourdomain.com
   • Multiple services on one IP
   • Password protect admin interfaces
   • Automatic HTTPS for everything
"""
    
    return message