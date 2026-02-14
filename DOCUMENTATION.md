# ORCHIX - Complete Documentation

<p align="center">
  <img src="web/static/favicon.svg?v=1.2" width="100" height="100" alt="ORCHIX Logo">
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
5. [User Management](#user-management)
6. [Application Templates](#application-templates)
7. [Backup & Restore](#backup--restore)
8. [Server Migration](#server-migration)
9. [License Management](#license-management)
10. [Security](#security)
11. [API Reference](#api-reference)
12. [Troubleshooting](#troubleshooting)
13. [Advanced Configuration](#advanced-configuration)

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
2. An admin user is created on first run with a random password shown in the terminal:
   ```
   Admin user created. Username: admin, Password: randompassword123
   ```
3. Login with username `admin` and the generated password
4. Change password in Settings or create additional users (PRO: unlimited, FREE: 1 user)

### Dashboard

- **Lily Theme**: Modern dark theme with pink (#ec4899) and teal (#14b8a6) accents
- **Multi-User RBAC**: Admin, Operator, Viewer roles with permission-based UI
- **Real-time Updates**: Server-Sent Events (SSE) for live container status
- **System Overview**: CPU, RAM, disk, network monitoring
- **Grid View**: Visual cards per application
- **Filters**: Search by name, category, status
- **Sidebar Collapse**: Responsive layout for better space management
- **User Management** (Admin only): Create, edit, and delete users with role assignment

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

## User Management

### Roles

ORCHIX uses Role-Based Access Control (RBAC) with three roles:

| Role | Description |
|------|-------------|
| **Admin** | Full access. Can manage users, licenses, system updates, and all operations. |
| **Operator** | Can manage containers, apps, backups, and migrations. Cannot manage users or system settings. |
| **Viewer** | Read-only access. Can view dashboards, logs, and container status. Cannot perform any actions. |

### Managing Users (Admin only)

**Web UI:**
1. Navigate to **Users** in the sidebar (Admin only)
2. View all users with their roles and last login
3. Click **Add User** to create a new user
4. Click on a user to edit role or reset password
5. Click **Delete** to remove a user

**Rules:**
- Usernames must be 3-32 characters, lowercase alphanumeric with `-` and `_`
- Passwords must be 8-1024 characters
- Cannot delete yourself or the last admin
- Cannot demote the last admin

### User Limits

- **FREE**: 1 user (the initial admin)
- **PRO**: Unlimited users

### License Downgrade Behavior

When a PRO license expires or is deactivated:
- **Existing containers keep running** and can be started/stopped/restarted
- **New container creation** is blocked when over the FREE limit (3)
- **Only admin users can log in** on FREE tier - other users are blocked with a clear message
- **New user creation** is blocked
- **PRO features** (backups, migration, audit) become inaccessible
- No data is deleted - existing containers, users, and backups remain intact

### First Setup

On first run, ORCHIX creates an `admin` user with a randomly generated password displayed in the terminal. If you're migrating from an older single-password version, the existing password is automatically migrated to an admin user.

### Password Reset

Any user can change their own password via the Web UI sidebar menu. Admins can reset any user's password via the Users panel.

To reset all users (emergency):
```bash
# Delete user database - a new admin will be created on restart
rm ~/.orchix_web_users.json        # Linux
del %USERPROFILE%\.orchix_web_users.json  # Windows
python main.py --web
```

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
  "name": "wordpress",
  "display_name": "WordPress",
  "description": "Open-source CMS and blogging platform",
  "icon": "📝",
  "category": "Web",
  "version": "6.x",
  "image": "wordpress:latest",
  "image_size_mb": 260,
  "license_required": null,
  "ports": [
    {"container": 80, "default_host": 8080, "label": "HTTP"}
  ],
  "volumes": [
    {"name_suffix": "data", "mount": "/var/www/html"}
  ],
  "env": [
    {"key": "WORDPRESS_DB_HOST", "label": "Database Host", "default": "localhost:3306", "required": true},
    {"key": "WORDPRESS_DB_USER", "label": "Database User", "default": "wordpress", "required": true},
    {"key": "WORDPRESS_DB_PASSWORD", "label": "Database Password", "type": "password", "generate": true},
    {"key": "WORDPRESS_DB_NAME", "label": "Database Name", "default": "wordpress", "required": true}
  ],
  "restart": "unless-stopped"
}
```

### Custom Templates

To add your own application template, edit `apps/templates.json`:

1. Open `apps/templates.json`
2. Add your template to the "templates" array:

```json
{
  "name": "myapp",
  "display_name": "My Application",
  "description": "My custom application",
  "icon": "🚀",
  "category": "Custom",
  "version": "1.0",
  "image": "myapp:latest",
  "image_size_mb": 100,
  "license_required": null,
  "ports": [
    {"container": 9000, "default_host": 9000, "label": "Web UI"}
  ],
  "volumes": [
    {"name_suffix": "data", "mount": "/data"}
  ],
  "env": [
    {"key": "MY_ENV_VAR", "label": "Environment Variable", "default": "value"}
  ],
  "restart": "unless-stopped"
}
```

3. Restart ORCHIX to see your custom application in the list

**Note:** Docker Compose files are generated automatically from the template definition. You don't need to create separate `.yml` files.

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
# Create backup (requires operator or admin role)
curl -X POST http://localhost:5000/api/backup/<container_name> \
  -b cookies.txt -H "X-CSRFToken: TOKEN"

# List backups
curl http://localhost:5000/api/backups/<container_name> \
  -b cookies.txt

# Restore backup (requires operator or admin role)
curl -X POST http://localhost:5000/api/restore/<container_name>/<timestamp> \
  -b cookies.txt -H "X-CSRFToken: TOKEN"
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
| **Users** | 1 | Unlimited |
| **RBAC Roles** | — | Admin, Operator, Viewer |
| **Web UI** | ✓ | ✓ |
| **CLI** | ✓ | ✓ |
| **Real-time Monitoring** | ✓ | ✓ |
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

### Authentication & Authorization

**Multi-User RBAC:**
- 3 roles: **Admin**, **Operator**, **Viewer**
- Backend permission enforcement on all API endpoints (`@require_permission`)
- Frontend hides unauthorized actions based on user role
- User data stored in `~/.orchix_web_users.json` with atomic writes

| Capability | Admin | Operator | Viewer |
|-----------|-------|----------|--------|
| View dashboard, containers, logs | ✓ | ✓ | ✓ |
| Start/stop/restart containers | ✓ | ✓ | ✗ |
| Install/update/uninstall apps | ✓ | ✓ | ✗ |
| Edit compose files | ✓ | ✓ | ✗ |
| Backup & restore (PRO) | ✓ | ✓ | ✗ |
| Delete backups (PRO) | ✓ | ✗ | ✗ |
| Migration (PRO) | ✓ | ✓ | ✗ |
| Manage users | ✓ | ✗ | ✗ |
| License & system update | ✓ | ✗ | ✗ |
| Change own password | ✓ | ✓ | ✓ |

**Password Security:**
- PBKDF2-SHA256 hashing (Werkzeug, 100k+ iterations)
- Minimum 8 characters, maximum 1024 characters
- Rate limiting: 5 login attempts per 5 minutes per IP
- Session timeout: 8 hours

**User Limits:**
- FREE: 1 user (single admin)
- PRO: Unlimited users

**CSRF Protection:**
- Flask-WTF with double-submit cookie pattern
- All state-changing API requests require `X-CSRFToken` header
- CSRF token injected via `<meta>` tag for SPA

### Input Validation

All inputs are sanitized against:
- **Path Traversal**: Blocks `../` sequences in filesystem and tarball extraction
- **YAML Injection**: Uses `yaml.safe_load()`
- **Command Injection**: Subprocess with list args (no shell)
- **Port Validation**: Only allows 1-65535
- **Container Names**: Regex validation (`^[a-zA-Z0-9][a-zA-Z0-9_.-]+$`)
- **Username Validation**: Regex (`^[a-z0-9][a-z0-9_-]{2,31}$`)
- **XSS Prevention**: HTML output escaping on all dynamic content

### Security Headers

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains  (when ORCHIX_HTTPS=true)
```

### File Security

- Secret key file (`~/.orchix_web_secret`): 0600 permissions
- User database (`~/.orchix_web_users.json`): 0600 permissions, atomic writes via temp file + rename
- Thread-safe file operations with `threading.Lock()`

### Audit Logging (PRO)

All actions are logged with the authenticated username:

```json
{
  "timestamp": "2026-02-14T14:30:22Z",
  "user": "admin",
  "action": "container_start",
  "target": "wordpress-prod",
  "ip": "192.168.1.100",
  "success": true
}
```

Tracked events include: container operations, app installs/updates, backup/restore, user management (create/delete/role change), password changes, system updates, login attempts.

View logs:
```bash
# Web UI: Navigate to Audit tab (PRO)

# API
curl http://localhost:5000/api/audit/logs \
  -b cookies.txt
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

All API requests require session authentication. State-changing requests (POST/PUT/DELETE) also require a CSRF token.

```bash
# Login with username + password to get session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin&password=your_password&csrf_token=TOKEN' \
  -c cookies.txt

# Use session cookie for GET requests
curl http://localhost:5000/api/containers \
  -b cookies.txt

# POST/PUT/DELETE requests need X-CSRFToken header
curl -X POST http://localhost:5000/api/containers/myapp/start \
  -b cookies.txt \
  -H "X-CSRFToken: TOKEN"
```

**Permission enforcement:** Each endpoint requires specific permissions. Requests without sufficient permissions return `403 Forbidden`.

### Endpoints

#### Users (Admin only)

**Get current user info:**
```bash
GET /api/auth/me
# Returns: { username, role, permissions[] }
```

**List all users:**
```bash
GET /api/users
```

**Create user:**
```bash
POST /api/users
{ "username": "operator1", "password": "securepass", "role": "operator" }
```

**Update user:**
```bash
PUT /api/users/<username>
{ "role": "viewer" }  # or { "password": "newpass" }
```

**Delete user:**
```bash
DELETE /api/users/<username>
```

**Change own password (any role):**
```bash
POST /api/auth/change-password
{ "current_password": "old", "new_password": "new" }
```

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
# Delete user database file (a new admin user with random password will be created)
rm ~/.orchix_web_users.json  # Linux
del %USERPROFILE%\.orchix_web_users.json  # Windows

# Restart ORCHIX - new admin user will be generated
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
# Web UI
WEB_PORT=5000
WEB_HOST=0.0.0.0

# HTTPS mode (enables Secure cookie flag + HSTS header)
ORCHIX_HTTPS=true

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

### Multi-language Support

The ORCHIX Web UI is currently English-only. Multi-language support (DE/EN/EL) is available on the [payment website](https://orchix.dev) but not in the ORCHIX application itself.

### Performance Tuning

**Docker Resource Limits:**

Edit container's `docker-compose.yml` to limit resources:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
```

**Storage Optimization:**

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# View disk usage
docker system df
```

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
- Support: [support@orchix.dev](mailto:support@orchix.dev)

---

## License

ORCHIX is commercial software.

- **FREE Tier**: Free for personal use (max 3 containers, 1 user)
- **PRO Tier**: €29/month commercial license with unlimited containers and users

Purchase at: [https://orchix.dev](https://orchix.dev)

---

## Changelog

### v1.2 (2026-02-14)
- Added Web UI with modern lily theme (Inter font, pink/teal design)
- **Multi-User RBAC** with 3 roles: Admin, Operator, Viewer
- **CSRF protection** via Flask-WTF
- **Security hardening**: CSP headers, HSTS, tarball path traversal protection, XSS prevention, thread-safe file ops, file permission hardening
- Template system for 30 applications
- Backup & Restore functionality (PRO)
- Server Migration (PRO)
- Audit logging with per-user tracking (PRO)
- Real-time system monitoring dashboard with SSE
- One-click update from Web UI

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
