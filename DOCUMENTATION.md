# ORCHIX - Complete Documentation

<p align="center">
  <img src="web/static/favicon.svg" width="100" height="100" alt="ORCHIX Logo">
</p>

**Version:** 1.2
**License:** Commercial (€29/month)
**Platform:** Linux, Windows (WSL2)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [CLI Usage](#cli-usage)
4. [Web UI Usage](#web-ui-usage)
5. [Application Templates](#application-templates)
6. [Backup & Restore](#backup--restore)
7. [Server Migration](#server-migration)
8. [License Management](#license-management)
9. [Security](#security)
10. [API Reference](#api-reference)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Configuration](#advanced-configuration)

---

## Getting Started

### What is ORCHIX?

ORCHIX is a container management system that simplifies Docker operations through:
- **30 pre-configured applications** (WordPress, Nextcloud, n8n, PostgreSQL, etc.)
- **CLI + Web UI** for flexible management
- **One-click deployment** with automatic port management
- **Backup & Migration** tools (PRO)
- **Audit logging** for compliance (PRO)

### Who is it for?

- Small teams without dedicated DevOps
- System administrators managing multiple services
- Developers who want to focus on code, not infrastructure

---

## Installation

### Prerequisites

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **OS** | Ubuntu 20.04, Debian 11, Windows 10 | Ubuntu 22.04, Windows 11 |
| **Python** | 3.8+ | 3.11+ |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 20 GB free | 50 GB free |
| **Docker** | 20.10+ | Latest |

### Quick Install

#### Linux

```bash
# Clone repository
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX

# Install dependencies
pip3 install -r requirements.txt

# Run ORCHIX
sudo python3 main.py
```

#### Windows (PowerShell as Administrator)

```powershell
# Clone repository
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX

# Install dependencies
pip install -r requirements.txt

# Run ORCHIX
python main.py
```

### Docker Auto-Installation

If Docker is not installed, ORCHIX will offer to install it automatically:

**Linux:**
```bash
# ORCHIX Menu > System Setup > Install Docker
# Runs: curl -fsSL https://get.docker.com | sh
```

**Windows:**
- Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- Enable WSL2 integration
- Restart ORCHIX

---

## CLI Usage

### Launch CLI

```bash
python main.py
```

### Main Menu

```
╭─────────────────────────────────────╮
│          ORCHIX v1.2                │
│   Container Management System       │
╰─────────────────────────────────────╯

1. Install Applications
2. Manage Containers
3. Backup & Restore (PRO)
4. Server Migration (PRO)
5. System Dashboard
6. License Management
7. System Setup
8. Exit
```

### Dashboard

```bash
# Real-time system monitoring
python main.py
# Select: 5. System Dashboard
```

Shows:
- CPU, RAM, Disk usage
- Network traffic per interface
- Running containers
- Container resource consumption

### Install Application

```bash
# Interactive installation
python main.py
# Select: 1. Install Applications
# Choose application > Configure port > Deploy
```

Example: Install WordPress

```
Select application: WordPress
Enter port (default 8080): 8080
Install name: wordpress-prod

✓ Pulling images...
✓ Creating container...
✓ Starting services...

WordPress is ready at: http://localhost:8080
```

### Container Management

```bash
# Manage existing containers
python main.py
# Select: 2. Manage Containers
```

Operations:
- **Start/Stop/Restart** container
- **View Logs** (real-time)
- **Inspect** container details
- **Delete** container and volumes
- **Update** to latest image

---

## Web UI Usage

### Start Web UI

```bash
# Default port 5000
python main.py --web

# Custom port
python main.py --web --port 8080
```

### First Login

1. Open browser: `http://localhost:5000`
2. Password is shown in terminal on first run:
   ```
   Generated password: randompassword123
   ```
3. Login with password
4. Change password in System settings

### Dashboard

- **Grid View**: Visual cards per application
- **List View**: Compact table layout
- **Compact View**: Dense information display
- **Filters**: Search by name, category, status

### Install Application

1. Navigate to **Applications** tab
2. Click **Install** on desired app
3. Configure:
   - Installation name
   - Port number
   - Custom YAML (optional)
4. Click **Deploy**
5. Monitor installation progress
6. Access app via **Open** button

### Backup & Restore (PRO)

#### Create Backup

1. Navigate to **Containers** tab
2. Select container
3. Click **Backup** button
4. Backup is saved to: `backups/<container>/<timestamp>/`

Includes:
- All Docker volumes
- `docker-compose.yml`
- Metadata (timestamp, size, version)

#### Restore Backup

1. Navigate to **Backups** tab
2. Select backup
3. Click **Restore**
4. Container is recreated with restored data

### Server Migration (PRO)

#### Export Migration Package

1. Navigate to **Migration** tab
2. Select containers to migrate
3. Click **Export**
4. Download `.tar.gz` (Linux) or `.zip` (Windows)

Package contains:
- Backups of all selected containers
- `docker-compose.yml` files
- Migration manifest

#### Import Migration Package

1. Navigate to **Migration** tab
2. Upload migration package
3. Click **Import**
4. ORCHIX automatically:
   - Extracts package
   - Creates containers
   - Restores volumes
   - Starts services

---

## Application Templates

### Available Applications

#### Web & CMS
- **WordPress** - CMS platform
- **Nextcloud** - File sync & share
- **Nginx Proxy Manager** - Reverse proxy with SSL

#### Databases
- **PostgreSQL** - Relational database
- **MariaDB** - MySQL fork
- **Redis** - In-memory cache
- **InfluxDB** - Time-series DB
- **Qdrant** - Vector database

#### DevOps & Automation
- **n8n** - Workflow automation
- **Gitea** - Git server
- **Traefik** - Cloud-native reverse proxy
- **Watchtower** - Container auto-updater
- **Dozzle** - Docker log viewer

#### Monitoring
- **Grafana** - Metrics visualization
- **Uptime Kuma** - Uptime monitoring
- **Changedetection.io** - Website change detector

#### Security
- **Vaultwarden** - Password manager (Bitwarden)
- **Pi-hole** - Network-wide ad blocker

#### Media
- **Jellyfin** - Media server
- **Stirling PDF** - PDF tools
- **File Browser** - Web file manager

#### Tools
- **Adminer** - Database manager
- **phpMyAdmin** - MySQL admin
- **IT-Tools** - Developer utilities
- **Homer, Homarr, Heimdall** - Dashboards
- **Duplicati** - Backup software
- **MinIO** - Object storage
- **Eclipse Mosquitto** - MQTT broker

### Template Structure

Templates are defined in `apps/templates.json`:

```json
{
  "wordpress": {
    "name": "WordPress",
    "category": "Web & CMS",
    "description": "World's most popular CMS",
    "default_port": 8080,
    "install_size_mb": 450,
    "compose_template": "wordpress.yml",
    "ports": [
      {
        "container": 80,
        "host": 8080,
        "description": "Web UI"
      }
    ],
    "volumes": [
      "wordpress_data:/var/www/html"
    ],
    "env": {
      "WORDPRESS_DB_HOST": "db",
      "WORDPRESS_DB_USER": "wordpress",
      "WORDPRESS_DB_PASSWORD": "password123"
    }
  }
}
```

### Custom Templates

Create your own template:

```bash
# Add to apps/templates.json
{
  "myapp": {
    "name": "My Application",
    "category": "Custom",
    "description": "My custom app",
    "default_port": 9000,
    "compose_template": "myapp.yml"
  }
}

# Create apps/compose_templates/myapp.yml
version: '3.8'
services:
  myapp:
    image: myapp:latest
    ports:
      - "${PORT}:9000"
    volumes:
      - myapp_data:/data
volumes:
  myapp_data:
```

Reload ORCHIX to see your app.

---

## Backup & Restore

### Backup Strategy

**Automatic Backups (PRO):**
- Pre-update backups (before container updates)
- Scheduled backups (via cron/Task Scheduler)
- Manual backups (on-demand)

**What's Backed Up:**
- All Docker volumes
- Environment variables
- `docker-compose.yml`
- Container metadata

### Manual Backup (CLI)

```bash
python main.py
# Select: 3. Backup & Restore
# Select container > Create Backup

# Backup saved to:
# Linux: ~/.orchix/backups/<container>/<timestamp>/
# Windows: %USERPROFILE%\.orchix\backups\<container>\<timestamp>\
```

### Manual Restore (CLI)

```bash
python main.py
# Select: 3. Backup & Restore
# Select backup > Restore

# Stops container > Restores volumes > Restarts container
```

### Backup via API

```bash
# Create backup
curl -X POST http://localhost:5000/api/backup/<container_name> \
  -H "Authorization: Bearer YOUR_TOKEN"

# List backups
curl http://localhost:5000/api/backups/<container_name> \
  -H "Authorization: Bearer YOUR_TOKEN"

# Restore backup
curl -X POST http://localhost:5000/api/restore/<container_name>/<timestamp> \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Backup Format

```
backup_20260213_143022/
├── metadata.json         # Backup info (size, timestamp, version)
├── docker-compose.yml    # Original compose file
└── volumes/
    ├── volume1.tar.gz    # Compressed volume data
    └── volume2.tar.gz
```

---

## Server Migration

### Migration Workflow

```
Source Server          Migration Package          Target Server
     │                        │                         │
     ├──> Export ──────────> .tar.gz ──────────> Import ─┤
     │                        │                         │
   Backup                 Transfer                  Restore
 Containers                 File                   Containers
```

### Export (Source Server)

**CLI:**
```bash
python main.py
# Select: 4. Server Migration > Export
# Select containers > Choose output path

# Creates: migration_20260213.tar.gz
```

**Web UI:**
1. Navigate to **Migration** tab
2. Select containers
3. Click **Export Package**
4. Download file

**API:**
```bash
curl -X POST http://localhost:5000/api/migration/export \
  -H "Content-Type: application/json" \
  -d '{"containers": ["wordpress", "postgresql"]}' \
  --output migration.tar.gz
```

### Import (Target Server)

**CLI:**
```bash
python main.py
# Select: 4. Server Migration > Import
# Select migration package > Confirm import

# ORCHIX will:
# 1. Extract package
# 2. Create containers
# 3. Restore volumes
# 4. Start services
```

**Web UI:**
1. Navigate to **Migration** tab
2. Click **Import Package**
3. Upload migration file
4. Monitor import progress

**API:**
```bash
curl -X POST http://localhost:5000/api/migration/import \
  -F "file=@migration.tar.gz"
```

### Migration Package Contents

```
migration_20260213.tar.gz
├── manifest.json                    # Migration metadata
├── wordpress/
│   ├── backup/                      # Volume backups
│   └── docker-compose.yml
├── postgresql/
│   ├── backup/
│   └── docker-compose.yml
└── checksums.txt                    # Integrity verification
```

---

## License Management

### License Tiers

| Feature | FREE | PRO (€29/mo) |
|---------|------|--------------|
| **Applications** | All 30 | All 30 |
| **Containers** | Max 3 | Unlimited |
| **Web UI** | ✓ | ✓ |
| **CLI** | ✓ | ✓ |
| **Backup & Restore** | ✗ | ✓ |
| **Multi-Instance** | ✗ | ✓ |
| **Server Migration** | ✗ | ✓ |
| **Audit Logs** | ✗ | ✓ |
| **Support** | Community | Priority |

### Activate PRO License

**CLI:**
```bash
python main.py
# Select: 6. License Management > Activate License
# Enter license key: ORCHIX-PRO-XXXXXXXX-XXXXXXXX
# Enter email: your@email.com

# License validated and activated
```

**Web UI:**
1. Navigate to **License** tab
2. Enter license key
3. Enter email
4. Click **Activate**

**API:**
```bash
curl -X POST http://localhost:5000/api/license/activate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "ORCHIX-PRO-XXXXXXXX-XXXXXXXX",
    "email": "your@email.com"
  }'
```

### Purchase License

Visit: [https://orchix.dev/#pricing](https://orchix.dev/#pricing)

1. Click **Get Started - €29/month**
2. Enter email
3. Pay via Stripe
4. Receive license key via email
5. Activate in ORCHIX

### License Validation

ORCHIX validates licenses:
- **Online**: Checks with `orchix.dev` server every 24h
- **Offline**: Uses cached validation for up to 7 days
- **HMAC-signed**: License keys are cryptographically signed

License format:
```
ORCHIX-PRO-A3F9K2X7-D4E8C1B5
│      │   │        └─ HMAC signature
│      │   └─ Random component
│      └─ Tier (PRO/PRO_PLUS/ENTERPRISE)
└─ Prefix
```

---

## Security

### Authentication

**Web UI:**
- PBKDF2 password hashing (100,000 iterations)
- Session-based authentication
- 8-hour session timeout
- Rate limiting: 5 login attempts per 5 minutes

**API:**
- Same session authentication as Web UI
- Bearer token support (coming soon)

### Input Validation

All inputs are sanitized against:
- **Path Traversal**: Blocks `../` sequences
- **YAML Injection**: Uses `yaml.safe_load()`
- **Command Injection**: Subprocess with list args (no shell)
- **Port Validation**: Only allows 1-65535
- **SQL Injection**: Parameterized queries (SQLite)

### Security Headers

```http
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
```

### Audit Logging (PRO)

All actions are logged:

```json
{
  "timestamp": "2026-02-13T14:30:22Z",
  "user": "admin",
  "action": "container_start",
  "target": "wordpress-prod",
  "ip": "192.168.1.100",
  "success": true
}
```

View logs:
```bash
# CLI
python main.py
# Select: Audit Logs

# API
curl http://localhost:5000/api/audit/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Reporting Security Issues

Email: [security@orchix.dev](mailto:security@orchix.dev)

Do NOT create public GitHub issues for security vulnerabilities.

---

## API Reference

### Base URL

```
http://localhost:5000/api
```

### Authentication

All API requests require authentication:

```bash
# Login to get session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your_password"}' \
  -c cookies.txt

# Use session cookie in subsequent requests
curl http://localhost:5000/api/containers \
  -b cookies.txt
```

### Endpoints

#### Containers

**List all containers:**
```bash
GET /api/containers
```

Response:
```json
[
  {
    "name": "wordpress-prod",
    "status": "running",
    "ports": ["8080:80"],
    "image": "wordpress:latest",
    "created": "2026-02-13T10:00:00Z"
  }
]
```

**Start container:**
```bash
POST /api/container/<name>/start
```

**Stop container:**
```bash
POST /api/container/<name>/stop
```

**View logs:**
```bash
GET /api/container/<name>/logs?tail=100
```

**Delete container:**
```bash
DELETE /api/container/<name>
```

#### Applications

**List templates:**
```bash
GET /api/templates
```

**Install application:**
```bash
POST /api/install
Content-Type: application/json

{
  "template": "wordpress",
  "name": "my-wordpress",
  "port": 8080
}
```

#### Backup (PRO)

**Create backup:**
```bash
POST /api/backup/<container_name>
```

**List backups:**
```bash
GET /api/backups/<container_name>
```

**Restore backup:**
```bash
POST /api/restore/<container_name>/<timestamp>
```

#### Migration (PRO)

**Export package:**
```bash
POST /api/migration/export
Content-Type: application/json

{
  "containers": ["wordpress", "postgresql"]
}
```

**Import package:**
```bash
POST /api/migration/import
Content-Type: multipart/form-data

file=@migration.tar.gz
```

#### System

**System stats:**
```bash
GET /api/system/stats
```

Response:
```json
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 71.5,
  "containers_total": 5,
  "containers_running": 3
}
```

**Check for updates:**
```bash
GET /api/system/update-check
```

---

## Troubleshooting

### Docker not found

**Error:**
```
Docker is not installed or not running
```

**Solution:**

Linux:
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo usermod -aG docker $USER
# Logout and login again
```

Windows:
1. Install Docker Desktop
2. Enable WSL2 integration
3. Restart ORCHIX

### Permission denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

Linux:
```bash
# Run with sudo
sudo python3 main.py

# OR add user to docker group
sudo usermod -aG docker $USER
# Logout and login
```

Windows:
- Run PowerShell as Administrator

### Port already in use

**Error:**
```
Port 8080 is already in use
```

**Solution:**
1. Choose different port during installation
2. Or stop conflicting service:
   ```bash
   # Find process using port
   sudo lsof -i :8080  # Linux
   netstat -ano | findstr :8080  # Windows

   # Kill process
   sudo kill -9 <PID>
   ```

### Module not found

**Error:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Web UI password forgotten

**Solution:**
```bash
# Delete password file
rm ~/.orchix_web_password  # Linux
del %USERPROFILE%\.orchix_web_password  # Windows

# Restart ORCHIX - new password will be generated
python main.py --web
```

### Container won't start

**Check logs:**
```bash
# CLI
python main.py
# Select: Manage Containers > Select container > View Logs

# OR direct Docker command
docker logs <container_name>
```

**Common issues:**
- Port conflict → Change port
- Volume permission → `chmod` or run as root
- Missing environment variable → Check `.env` file
- Image not found → Pull manually: `docker pull <image>`

---

## Advanced Configuration

### Environment Variables

Create `.env` file in ORCHIX root:

```bash
# Database
DB_PATH=~/.orchix/data.db

# Web UI
WEB_PORT=5000
WEB_HOST=0.0.0.0
SECRET_KEY=your-secret-key-here

# License
LICENSE_SIGNING_SECRET=your-signing-secret

# Paths
BACKUP_PATH=~/.orchix/backups
MIGRATION_PATH=~/.orchix/migrations
```

### Custom Docker Networks

ORCHIX creates isolated networks per app by default. To use custom networks:

1. Edit app's `docker-compose.yml`:
   ```yaml
   networks:
     custom_network:
       external: true
   ```

2. Create network:
   ```bash
   docker network create custom_network
   ```

3. Reinstall app in ORCHIX

### Systemd Service (Linux)

Auto-start ORCHIX on boot:

```bash
sudo nano /etc/systemd/system/orchix.service
```

```ini
[Unit]
Description=ORCHIX Container Management
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=orchix
WorkingDirectory=/opt/orchix
ExecStart=/usr/bin/python3 /opt/orchix/main.py --web --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable orchix
sudo systemctl start orchix
```

### Windows Task Scheduler

Auto-start ORCHIX on boot:

1. Open Task Scheduler
2. Create Task:
   - **Name**: ORCHIX
   - **Trigger**: At startup
   - **Action**: Start program
     - Program: `python`
     - Arguments: `C:\orchix\main.py --web --port 5000`
     - Start in: `C:\orchix`
   - **Run with highest privileges**

### Nginx Reverse Proxy

Expose ORCHIX Web UI via domain:

```nginx
server {
    listen 80;
    server_name orchix.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name orchix.example.com;

    ssl_certificate /etc/letsencrypt/live/orchix.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/orchix.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for real-time updates)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Custom Hooks

Add hooks for backup/restore events:

Create `apps/hooks/<app_name>.py`:

```python
def before_backup(container_name):
    """Run before backup"""
    print(f"Preparing {container_name} for backup...")
    # Example: Flush database to disk
    os.system(f"docker exec {container_name} pg_dump > /tmp/backup.sql")

def after_restore(container_name):
    """Run after restore"""
    print(f"Finalizing {container_name} restore...")
    # Example: Clear cache
    os.system(f"docker exec {container_name} rm -rf /var/cache/*")
```

ORCHIX will automatically load and execute hooks.

---

## Support

### Community Support (FREE)

- GitHub Issues: [github.com/Sad-without-you/ORCHIX/issues](https://github.com/Sad-without-you/ORCHIX/issues)
- GitHub Discussions: [github.com/Sad-without-you/ORCHIX/discussions](https://github.com/Sad-without-you/ORCHIX/discussions)

### Priority Support (PRO)

- Email: [support@orchix.dev](mailto:support@orchix.dev)
- Response time: <24h (weekdays)
- Direct help with:
  - Installation issues
  - Migration assistance
  - Custom template development
  - Performance optimization

### Contact

- General inquiries: [contact@orchix.dev](mailto:contact@orchix.dev)
- Security issues: [security@orchix.dev](mailto:security@orchix.dev)
- Sales: [sales@orchix.dev](mailto:sales@orchix.dev)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## License

ORCHIX is commercial software. See [LICENSE](LICENSE) for details.

- **FREE Tier**: Free for personal use (max 3 containers)
- **PRO Tier**: €29/month commercial license

Purchase at: [https://orchix.dev](https://orchix.dev)

---

## Changelog

### v1.2 (2026-02-13)
- Added Web UI with modern interface
- Template system for 30 applications
- Backup & Restore functionality (PRO)
- Server Migration (PRO)
- Audit logging (PRO)
- Security hardening (PBKDF2, input validation)
- Multi-language support (DE/EN/EL)

### v1.1 (2026-01-15)
- Initial release
- CLI interface
- Basic container management
- 20 application templates

---

**Website:** [orchix.dev](https://orchix.dev)
**GitHub:** [github.com/Sad-without-you/ORCHIX](https://github.com/Sad-without-you/ORCHIX)
**Creator:** [Georgios Sevastakis](https://www.linkedin.com/in/georgios-sevastakis-578a02322/)

© 2026 ORCHIX - All Rights Reserved
