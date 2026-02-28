# ORCHIX - Complete Documentation

<p align="center">
  <img src="web/static/favicon.svg?v=1.4" width="100" height="100" alt="ORCHIX Logo">
</p>

**Version:** 1.4
**License:** Commercial (€29/month)
**Platform:** Linux, Windows (WSL2 / native)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [CLI Usage](#cli-usage)
4. [Web UI Usage](#web-ui-usage)
5. [User Management](#user-management)
6. [Application Templates](#application-templates)
7. [Database Discovery](#database-discovery)
8. [Backup & Restore](#backup--restore)
9. [Server Migration](#server-migration)
10. [License Management](#license-management)
11. [Security](#security)
12. [API Reference](#api-reference)
13. [Troubleshooting](#troubleshooting)
14. [Advanced Configuration](#advanced-configuration)

---

## Getting Started

### What is ORCHIX?

ORCHIX is a container management system that simplifies Docker operations through:
- **30 pre-configured applications** (WordPress, Nextcloud, n8n, PostgreSQL, etc.)
- **CLI + Web UI** for flexible management
- **One-click deployment** with automatic port management
- **Dynamic database discovery** — apps that need a database auto-detect available DB containers
- **Global orchix network** — all ORCHIX containers communicate by container name
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
curl -sSL https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.sh | bash
```

#### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/Sad-without-you/Orchix/main/install.ps1 | iex
```

The installer asks at the end if you want to start the Web UI immediately and enable autostart on login/boot.

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

## Background Service

The Web UI can run as a background service — no terminal needs to stay open.

### Service Commands

```bash
# Windows
orchix.ps1 service start    # Start Web UI in background
orchix.ps1 service stop     # Stop
orchix.ps1 service status   # Check if running (shows PID)
orchix.ps1 service enable   # Enable autostart on login (Registry)
orchix.ps1 service disable  # Disable autostart
orchix.ps1 service uninstall  # Remove service entries only

# Linux
orchix service start
orchix service stop
orchix service status
orchix service enable       # Enable autostart via systemd user service
orchix service disable
orchix service uninstall
```

Once started, open `http://localhost:5000` — the terminal can be closed.

### Uninstall ORCHIX

```powershell
# Windows — run in the ORCHIX folder:
.\uninstall.ps1
```
```bash
# Linux:
bash ./uninstall.sh
```

Both uninstallers:
1. Stop and remove the background service
2. Remove PATH entry / global symlink
3. Ask whether to delete config/data (`~/.orchix_configs/`)
4. Ask whether to delete the ORCHIX installation folder

---

## CLI Usage

### Launch CLI

```bash
./orchix.sh          # Linux
orchix.ps1           # Windows
```

### Main Menu

```
╭──────────────────────────────────────────────────────╮
│  Welcome to ORCHIX! | FREE    Containers: 2/3        │
╰──────────────────────────────────────────────────────╯

1. Dashboard
2. Install Applications
3. Update Applications
4. Uninstall Applications
5. Container Management
6. Backup & Restore (PRO only)
7. Server Migration (PRO only)
8. Audit Logs (PRO only)
9. License Manager
10. System Setup
11. Exit
```

PRO users see Backup, Migration, and Audit Logs without the "(PRO only)" label.

### Dashboard

Shows real-time system stats:
- CPU, RAM, disk usage
- Network traffic per interface
- Running containers with resource usage

### Install Application

```bash
./orchix.sh          # Linux
orchix.ps1           # Windows
# Select: 2. Install Applications
# Choose application > Configure settings > Deploy
```

When installing apps that require a database (e.g. WordPress, phpMyAdmin), ORCHIX automatically detects running database containers on the orchix network and pre-fills connection details. See [Database Discovery](#database-discovery).

### Container Management

Operations available:
- **Start / Stop / Restart**
- **View Logs** (real-time)
- **Inspect** container details
- **Delete** container and volumes
- **Update** to latest image

---

## Web UI Usage

### Start Web UI

**Background (recommended) — terminal can be closed:**
```bash
orchix.ps1 service start    # Windows
orchix service start        # Linux
```

**Foreground — terminal must stay open:**
```bash
./orchix.sh --web             # Linux – port 5000
./orchix.sh --web --port 8080 # Linux – custom port
orchix.ps1 --web              # Windows – port 5000
orchix.ps1 --web --port 8080  # Windows – custom port
```

Then open: `http://localhost:5000` (or replace `localhost` with your server IP)

### First Login

1. Open browser: `http://<server-ip>:5000`
2. On first run, ORCHIX creates an `admin` user with a random password printed in the terminal:
   ```
   Admin user created. Username: admin, Password: <random>
   ```
3. Login with `admin` and the generated password
4. Change password via the sidebar (bottom-left user section)

### Web UI Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `#/dashboard` | System stats, container cards, real-time monitoring |
| Containers | `#/containers` | Start/stop/restart/logs/inspect/edit compose |
| Applications | `#/apps` | Install new apps from the template store |
| Backups | `#/backups` | PRO: Create, restore, delete backups |
| Migration | `#/migration` | PRO: Export/import containers between servers |
| Audit Logs | `#/audit` | PRO: View user activity and system events |
| License | `#/license` | Activate/deactivate PRO license, view features |
| Users | `#/users` | Admin only: Manage user accounts and roles |

### Install Application (Web UI)

1. Navigate to **Applications**
2. Click **Install** on the desired app
3. Configure:
   - Instance name
   - Port number
   - Database host (auto-detected if a compatible DB is running — see [Database Discovery](#database-discovery))
   - Additional environment variables
4. Click **Install**
5. Monitor real-time installation progress via the progress bar
6. Access the app via the **Open** button once installation completes

### Sidebar

- **License badge** (top): Shows FREE or PRO status
- **Navigation**: Links to all pages; PRO-locked pages are visually dimmed for FREE users
- **Quick links**: Documentation, GitHub, Support (PRO only)
- **User section** (bottom): Username, role, logout button

---

## User Management

### Roles

ORCHIX uses Role-Based Access Control (RBAC) with three roles:

| Role | Description |
|------|-------------|
| **Admin** | Full access. Manages users, licenses, system settings, and all operations. |
| **Operator** | Manages containers, apps, backups, and migrations. Cannot manage users or system settings. |
| **Viewer** | Read-only access. Views dashboard, logs, and container status. Cannot take any actions. |

### Permissions Matrix

| Capability | Admin | Operator | Viewer |
|-----------|:-----:|:--------:|:------:|
| View dashboard & container status | ✓ | ✓ | ✓ |
| View container logs | ✓ | ✓ | ✓ |
| Inspect containers | ✓ | ✓ | ✓ |
| Start / stop / restart containers | ✓ | ✓ | ✗ |
| Install / update / uninstall apps | ✓ | ✓ | ✗ |
| View & edit compose files | ✓ | ✓ | ✗ |
| Create & restore backups (PRO) | ✓ | ✓ | ✗ |
| Delete backups (PRO) | ✓ | ✗ | ✗ |
| Server migration (PRO) | ✓ | ✓ | ✗ |
| View audit logs (PRO) | ✓ | ✓ | ✓ |
| Manage users | ✓ | ✗ | ✗ |
| License & system updates | ✓ | ✗ | ✗ |
| Change own password | ✓ | ✓ | ✓ |

### Managing Users (Admin only)

**Web UI:**
1. Navigate to **Users** (Admin only — hidden for other roles)
2. View all users, their roles, and last login time
3. Click **Add User** to create a new user
4. Click the actions menu on a user to edit role or reset password
5. Click **Delete** to remove a user

**Rules:**
- Usernames: 3–32 characters, lowercase alphanumeric with `-` and `_`
- Passwords: 8–1024 characters
- Cannot delete yourself or the last admin
- Cannot demote the last admin to a lower role

### User Limits

- **FREE**: 1 user (the initial admin only)
- **PRO**: Up to 3 users (Admin + Operator + Viewer, any combination)

### License Downgrade Behavior

When a PRO license expires or is deactivated:
- **Existing containers keep running** and can be started/stopped/restarted
- **New container creation** is blocked when at the FREE limit (3)
- **Only the admin user can log in** — Operator and Viewer accounts are blocked with a clear message
- **New user creation** is blocked
- **PRO features** (backups, migration, audit) become inaccessible
- **No data is deleted** — containers, users, and backups remain intact

If you had more than 3 containers when PRO expires, ORCHIX prompts you to select which 3 to keep managing. See [Container Selection](#container-selection-free-tier-downgrade).

### Password Reset (Emergency)

```bash
# Delete the user database — a new admin with a random password is created on restart
rm ~/.orchix_web_users.json           # Linux
del %USERPROFILE%\.orchix_web_users.json  # Windows
python main.py --web
```

---

## Application Templates

### Available Applications (30 total)

#### Web & CMS
| App | Description | Default Port |
|-----|-------------|-------------|
| **WordPress** 📝 | Open-source CMS and blogging platform | 8080 |
| **Nextcloud** ☁️ | Self-hosted cloud storage solution | 8085 |
| **Nginx Proxy Manager** 🔒 | Easy SSL reverse proxy with Let's Encrypt | 8080 / 8081 / 8443 |
| **Traefik** 🔀 | Modern reverse proxy and load balancer | 80 / 443 / 8081 |

#### Databases
| App | Description | Default Port |
|-----|-------------|-------------|
| **MariaDB** 🗃️ | Popular MySQL-compatible relational database | 3306 |
| **PostgreSQL** 🐘 | Open source relational database | 5432 |
| **Redis** 🔴 | In-memory data structure store and cache | 6379 |
| **InfluxDB** 📈 | Time-series database for metrics | 8086 |
| **Qdrant** 🔍 | Vector similarity search engine | 6333 / 6334 |

#### DevOps & Automation
| App | Description | Default Port |
|-----|-------------|-------------|
| **n8n** ⚡ | Workflow automation platform | 5678 |
| **Gitea** 🦊 | Lightweight self-hosted Git service | 3000 / 2222 (SSH) |
| **Watchtower** 🔄 | Automatic Docker container updates | — |
| **Dozzle** 📋 | Real-time Docker container log viewer | 8080 |

#### Monitoring
| App | Description | Default Port |
|-----|-------------|-------------|
| **Grafana** 📊 | Monitoring and observability platform | 3000 |
| **Uptime Kuma** 📡 | Self-hosted uptime monitoring tool | 3001 |
| **Changedetection.io** 👁️ | Website change detection and monitoring | 5000 |

#### Security
| App | Description | Default Port |
|-----|-------------|-------------|
| **Vaultwarden** 🔐 | Lightweight Bitwarden-compatible password manager | 8080 |
| **Pi-hole** 🛡️ | Network-wide ad blocking DNS server | 8080 / 53 (DNS) |

#### Storage
| App | Description | Default Port |
|-----|-------------|-------------|
| **MinIO** 💾 | S3-compatible object storage server | 9000 / 9001 |
| **File Browser** 📁 | Web-based file manager with sharing | 8080 |
| **Duplicati** 💿 | Encrypted cloud backup solution | 8200 |

#### Media & Tools
| App | Description | Default Port |
|-----|-------------|-------------|
| **Jellyfin** 🎬 | Free Software Media Server | 8096 |
| **Stirling PDF** 📄 | Open-source PDF tools | 8080 |
| **IT-Tools** 🛠️ | Collection of handy tools for developers | 8080 |
| **Eclipse Mosquitto** 📨 | Lightweight MQTT message broker for IoT | 1883 / 9001 |

#### Dashboards
| App | Description | Default Port |
|-----|-------------|-------------|
| **Homer** 🏡 | Simple static homepage for server services | 8080 |
| **Homarr** 🎯 | Customizable dashboard for your server | 7575 |
| **Heimdall** 🏠 | Application dashboard and launcher | 8080 |

#### Database Tools
| App | Description | Default Port |
|-----|-------------|-------------|
| **Adminer** 🗄️ | Multi-database management (MySQL, PostgreSQL, SQLite) | 8080 |
| **phpMyAdmin** 🐬 | Web interface for MySQL/MariaDB administration | 8080 |

### Template Structure

Templates are defined in `apps/templates.json`. Each template supports:

```json
{
  "name": "wordpress",
  "display_name": "WordPress",
  "description": "Open-source CMS and blogging platform",
  "icon": "📝",
  "category": "Web",
  "version": "6.x",
  "image": "wordpress:latest",
  "image_size_mb": 600,
  "license_required": null,
  "ports": [
    {"container": 80, "default_host": 8080, "label": "HTTP"}
  ],
  "volumes": [
    {"name_suffix": "data", "mount": "/var/www/html"}
  ],
  "env": [
    {"key": "WORDPRESS_DB_HOST", "label": "Database Host", "required": true,
     "role": "db_host", "db_types": ["mysql"]},
    {"key": "WORDPRESS_DB_USER", "label": "Database User",
     "db_credential": "user"},
    {"key": "WORDPRESS_DB_PASSWORD", "label": "Database Password",
     "type": "password", "generate": true, "db_credential": "password"},
    {"key": "WORDPRESS_DB_NAME", "label": "Database Name",
     "db_credential": "database"}
  ],
  "restart": "unless-stopped"
}
```

**Special env field roles:**

| Field | Purpose |
|-------|---------|
| `"role": "db_host"` | Marks this field as a database host selector — triggers DB discovery |
| `"db_types": ["mysql"]` | Limits DB discovery to compatible types (mysql, postgres, redis, mongo, influxdb) |
| `"db_credential": "user"` | Auto-fills this field from the selected DB container's credentials |
| `"db_port": true` | Auto-fills this field with the correct port for the detected DB type |
| `"generate": true` | Auto-generates a secure random value |

### Custom Templates

To add your own application, add an entry to `apps/templates.json` and restart ORCHIX:

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

Docker Compose files are generated automatically from the template — no `.yml` file needed.

---

## Database Discovery

When installing apps that require a database (WordPress, phpMyAdmin, Adminer, etc.), ORCHIX automatically detects running database containers on the `orchix` network and offers them for selection.

### How It Works

1. **On startup**, ORCHIX creates the global `orchix` Docker network and connects all managed containers to it.
2. **During app installation**, fields marked with `"role": "db_host"` trigger a database scan.
3. ORCHIX scans containers on the orchix network, detecting their type by image name:
   - `mariadb`, `mysql`, `percona` → MySQL-compatible
   - `postgres` → PostgreSQL
   - `redis` → Redis
   - `mongo` → MongoDB
   - `influxdb` → InfluxDB
4. Results are filtered by `db_types` so incompatible databases are not shown (e.g. Redis will never appear as a MySQL host).

### What Gets Auto-Filled

When a DB container is detected and selected:

| Field | Source |
|-------|--------|
| Database Host | Container name (reachable via orchix network) |
| Database User | Read from container's compose file environment |
| Database Password | Read from container's compose file environment |
| Database Name | Read from container's compose file environment |
| Database Port | Detected from DB type (3306 MySQL, 5432 PostgreSQL, etc.) |

### Scenarios

**No DB found:**
- A warning is shown: *"No database containers found. Install MariaDB or MySQL first, or enter the hostname manually."*
- The text reflects the required DB type (not a generic message)
- You can still type a hostname manually

**One DB found:**
- The hostname is pre-filled automatically
- Credentials are loaded from that DB's compose file

**Multiple DBs found:**
- A dropdown lets you select which DB to use
- Switching selection re-loads credentials from the newly chosen DB

### The orchix Network

All containers installed via ORCHIX are automatically added to the `orchix` Docker network. This allows containers to communicate with each other by container name, without needing to expose ports on the host.

**Example:** WordPress connects to MariaDB via `mariadb:3306` (not `localhost:3306`).

```bash
# Manually inspect the orchix network
docker network inspect orchix

# Manually connect an existing container
docker network connect orchix <container_name>
```

---

## Backup & Restore

> **PRO feature** — requires an active PRO license.

### What Gets Backed Up

- All Docker volumes attached to the container
- `docker-compose.yml` file
- Backup metadata (timestamp, size, version)

### Create Backup

**CLI:**
```bash
python main.py
# Select: Backup & Restore > Create Backup > Select container
```

**Web UI:**
1. Navigate to **Backups**
2. Click **Create Backup** for the desired container
3. Monitor progress

### Restore Backup

**CLI:**
```bash
python main.py
# Select: Backup & Restore > Restore > Select backup
```

**Web UI:**
1. Navigate to **Backups**
2. Click **Restore** on a backup
3. The container is stopped, volumes are restored, container is restarted

### Backup Storage Format

```
backups/<container_name>/<timestamp>/
├── metadata.json         # Backup info (timestamp, version, container)
├── docker-compose.yml    # Compose file at time of backup
└── volumes/
    ├── v0/               # First volume (tar.gz inside)
    │   └── data.tar.gz
    └── v1/               # Second volume (multi-volume apps)
        └── data.tar.gz
```

Single-volume apps use a flat structure inside `volumes/`. Multi-volume apps (Pi-hole, Nginx, InfluxDB, etc.) use numbered `v0/`, `v1/`, ... subdirectories.

---

## Server Migration

> **PRO feature** — requires an active PRO license.

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
# Select: Server Migration > Export
# Select containers > Confirm
# Creates: migration_<timestamp>.tar.gz
```

**Web UI:**
1. Navigate to **Migration**
2. Select containers to export
3. Click **Export Package**
4. Download the `.tar.gz` file

### Import (Target Server)

**CLI:**
```bash
python main.py
# Select: Server Migration > Import
# Enter path to migration package
# ORCHIX extracts, recreates, and restores all containers
```

**Web UI:**
1. Navigate to **Migration**
2. Click **Import Package**
3. Upload the migration file
4. Monitor import progress via real-time SSE stream

### Migration Package Contents

```
migration_<timestamp>.tar.gz
├── manifest.json              # Migration metadata (ORCHIX version, containers)
├── wordpress/
│   ├── docker-compose.yml
│   └── volumes/
│       └── v0/
│           └── data.tar.gz
└── postgresql/
    ├── docker-compose.yml
    └── volumes/
        └── v0/
            └── data.tar.gz
```

### Cross-Platform Migration

Migration packages are compatible between Linux and Windows (WSL2). Volume data is always archived as `.tar.gz` regardless of the host OS.

---

## License Management

### License Tiers

| Feature | FREE | PRO (€29/mo) |
|---------|:----:|:------------:|
| **Applications** | All 30 | All 30 |
| **Containers** | Max 3 | Unlimited |
| **Users** | 1 | Up to 3 |
| **RBAC Roles** | — | Admin, Operator, Viewer |
| **Web UI** | ✓ | ✓ |
| **CLI** | ✓ | ✓ |
| **Real-time Monitoring** | ✓ | ✓ |
| **Database Discovery** | ✓ | ✓ |
| **Global orchix Network** | ✓ | ✓ |
| **Backup & Restore** | ✗ | ✓ |
| **Multi-Instance** | ✗ | ✓ |
| **Server Migration** | ✗ | ✓ |
| **Audit Logs** | ✗ | ✓ |
| **Priority Email Support** | ✗ | ✓ |

### Activate PRO License

**CLI:**
```bash
python main.py
# Select: License Manager > Upgrade to PRO
# Enter license key: ORCH-PRO-XXXXXXXXXXXXXXXX-XXXXXXXXXX
```

**Web UI:**
1. Navigate to **License**
2. Click **Upgrade to PRO**
3. Enter your license key
4. Click **Activate**

**API:**
```bash
curl -X POST http://localhost:5000/api/license/activate \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TOKEN" \
  -b cookies.txt \
  -d '{"license_key": "ORCH-PRO-XXXXXXXXXXXXXXXX-XXXXXXXXXX"}'
```

### Deactivate License

**CLI:**
```bash
python main.py
# Select: License Manager > Deactivate License
```

**Web UI:** License page > **Deactivate License**

After deactivation, if you have more than 3 containers, you will be prompted to select which 3 to keep managing.

### Purchase License

Visit: [https://orchix.dev/#pricing](https://orchix.dev/#pricing)

1. Click **Jetzt kaufen** / **Get Started**
2. Complete payment via Stripe
3. Receive your license key by email
4. Activate in ORCHIX

### Container Selection (FREE Tier Downgrade)

When a PRO license expires or is deactivated and you have more than 3 containers:

1. ORCHIX prompts you to select exactly 3 containers to manage
2. Unselected containers **stay running** on the server but are hidden from ORCHIX
3. Re-activating PRO makes all containers visible again automatically
4. The selection is stored at `~/.orchix_managed_containers.json`

**Web UI:** An unclosable modal appears with checkboxes.
**CLI:** An interactive prompt guides you through the selection.

**Important:**
- Only triggered when you have more than 3 containers
- Container limit applies to installs — you cannot install a 4th container on FREE
- Managed container list is cleared when PRO is activated

### License Format

```
ORCH-PRO-A3F8B2C1D4E9F601-8A2B4C6D1E
│    │   │                └─ HMAC signature (10 chars)
│    │   └─ Random component (16 hex chars, 64-bit entropy)
│    └─ Tier (PRO)
└─ Prefix
```

License keys are HMAC-signed. Validation requires an internet connection to the ORCHIX license server. A 3-day offline grace period applies when the server is unreachable.

---

## Security

### Authentication & Authorization

**Multi-User RBAC:**
- 3 roles: **Admin**, **Operator**, **Viewer**
- Backend permission enforcement on all API endpoints (`@require_permission`)
- Frontend hides unauthorized actions based on user role
- User data stored in `~/.orchix_web_users.json` with atomic writes and 0600 permissions

**Password Security:**
- PBKDF2-SHA256 hashing (Werkzeug, 100k+ iterations)
- Minimum 8 characters, maximum 1024 characters
- Rate limiting: 5 login attempts per 5 minutes per IP
- Session timeout: 8 hours
- HTTP-only session cookies

**CSRF Protection:**
- Flask-WTF with double-submit cookie pattern
- All state-changing requests require `X-CSRFToken` header
- Token injected via `<meta name="csrf-token">` for SPA

### Sensitive Data Access

Compose files contain database passwords and other credentials. Access is restricted:

| Role | Read Compose File | Edit Compose File |
|------|:-----------------:|:-----------------:|
| Admin | ✓ | ✓ |
| Operator | ✓ | ✓ |
| Viewer | ✗ | ✗ |

> **Recommendation:** For production deployments, use HTTPS via a reverse proxy (Nginx, Caddy) to encrypt traffic and prevent credential exposure on the network.

### Input Validation

All inputs are sanitized against:
- **Path Traversal**: Blocks `../` sequences in filesystem operations and tarball extraction
- **YAML Injection**: Uses `yaml.safe_load()`
- **Command Injection**: All subprocess calls use list args (no shell)
- **Port Validation**: Only 1–65535
- **Container Names**: Regex `^[a-zA-Z0-9][a-zA-Z0-9_.-]+$`
- **Usernames**: Regex `^[a-z0-9][a-z0-9_-]{2,31}$`
- **XSS Prevention**: HTML output escaping on all dynamic content (`esc()`)

### Security Headers

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains  (when ORCHIX_HTTPS=true)
```

### File Security

| File | Permissions | Description |
|------|-------------|-------------|
| `~/.orchix_web_secret` | 0600 | Flask session secret key |
| `~/.orchix_web_users.json` | 0600 | User database with hashed passwords |
| `~/.orchix_managed_containers.json` | User default | Container selection (FREE tier) |

All user database writes use atomic temp-file + rename to prevent data corruption.

### Audit Logging (PRO)

All actions are logged with the authenticated username:

```json
{
  "timestamp": "2026-02-20T14:30:22Z",
  "user": "admin",
  "action": "container_start",
  "target": "wordpress",
  "ip": "192.168.1.100",
  "success": true
}
```

Tracked events: container start/stop/restart/install/update/uninstall, backup/restore/delete, migration export/import, user create/delete/role-change, password changes, system updates, login attempts.

**View logs — Web UI:** Navigate to **Audit Logs** (PRO)

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
# 1. Get the CSRF token from the meta tag (after loading the page)
# or pass it via the login form

# 2. Login to obtain a session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password&csrf_token=TOKEN" \
  -c cookies.txt

# 3. Use session cookie for GET requests
curl http://localhost:5000/api/containers \
  -b cookies.txt

# 4. POST/PUT/DELETE also need the X-CSRFToken header
curl -X POST http://localhost:5000/api/containers/myapp/start \
  -b cookies.txt \
  -H "X-CSRFToken: TOKEN"
```

### Auth Endpoints

```bash
GET  /api/auth/me                     # Current user info (username, role, permissions)
POST /api/auth/change-password        # Change own password
     { "current_password": "old", "new_password": "new" }
```

### User Endpoints (Admin only)

```bash
GET    /api/users                     # List all users
POST   /api/users                     # Create user
       { "username": "op1", "password": "pass", "role": "operator" }
PUT    /api/users/<username>          # Update role or password
       { "role": "viewer" }  or  { "password": "newpass" }
DELETE /api/users/<username>          # Delete user
```

### Container Endpoints

```bash
GET  /api/containers                          # List managed containers
GET  /api/containers/selection-needed         # Check if FREE tier selection is needed
     # Returns: { "needed": true, "limit": 3 }
GET  /api/containers/all-for-selection        # All containers for selection UI (admin)
POST /api/containers/select                   # Save container selection
     { "selected": ["wordpress", "mariadb", "n8n"] }

POST /api/containers/<name>/start             # Start container
POST /api/containers/<name>/stop              # Stop container
POST /api/containers/<name>/restart           # Restart container
GET  /api/containers/<name>/logs?tail=100     # Container logs
GET  /api/containers/<name>/inspect           # Container details
GET  /api/containers/<name>/compose           # Read compose file (admin/operator)
POST /api/containers/<name>/compose           # Save compose file (admin/operator)
POST /api/containers/<name>/uninstall         # Delete container + volumes
```

### Application Endpoints

```bash
GET  /api/apps                                # List available apps
GET  /api/apps/<name>/config-schema           # Installation form fields
GET  /api/apps/check-conflicts?name=x&port=y # Check for naming/port conflicts
GET  /api/apps/db-candidates?db_types=mysql   # Discover compatible DB containers
GET  /api/apps/db-credentials/<container>     # Get credentials from a DB container

POST /api/apps/install-stream                 # Install app (Server-Sent Events stream)
     { "app_name": "wordpress", "instance_name": "my-wp",
       "config": { "port": 8080, "WORDPRESS_DB_HOST": "mariadb" } }

POST /api/apps/update                         # Update app to latest image
POST /api/apps/update-stream                  # Update with SSE progress
POST /api/apps/set-password                   # Set post-install password (e.g. Pi-hole)
```

### Backup Endpoints (PRO)

```bash
GET  /api/backups                             # List all backups
POST /api/backups/create                      # Create backup
     { "container_name": "wordpress" }
POST /api/backups/restore                     # Restore from backup
     { "container_name": "wordpress", "timestamp": "20260220_143022" }
POST /api/backups/delete                      # Delete a backup (admin only)
```

### Migration Endpoints (PRO)

```bash
GET  /api/migrations/containers               # List containers available for export
POST /api/migrations/export-stream           # Export migration package (SSE stream)
     { "containers": ["wordpress", "mariadb"] }
POST /api/migrations/import-stream           # Import migration package (SSE stream)
     Content-Type: multipart/form-data
     file=@migration.tar.gz
```

### License Endpoints

```bash
GET  /api/license                             # License info and features
POST /api/license/activate                    # Activate PRO license
     { "license_key": "ORCH-PRO-..." }
POST /api/license/deactivate                  # Deactivate license
```

### System Endpoints

```bash
GET  /api/system                              # System info (OS, Docker version, uptime)
GET  /api/system/check-update                # Check for ORCHIX updates (cached 24h)
POST /api/system/update                       # Update ORCHIX via git pull
```

### Audit Endpoints (PRO)

```bash
GET  /api/audit                               # Get audit log entries
GET  /api/audit/users                         # List users who have taken actions
GET  /api/audit/user-activity                 # Activity summary per user
POST /api/audit/clear                         # Clear all audit logs (admin only)
```

### Dashboard Endpoints

```bash
GET  /api/dashboard                           # System stats + container list
GET  /api/dashboard/stream                    # SSE stream for live updates
```

---

## Troubleshooting

### Docker not found

**Error:**
```
Docker is not installed or not running
```

**Solution — Linux:**
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo usermod -aG docker $USER
# Logout and login again
```

**Solution — Windows:**
1. Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Enable WSL2 integration
3. Restart ORCHIX

### Permission denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution — Linux:**
```bash
# Add user to docker group (recommended)
sudo usermod -aG docker $USER
# Logout and login, then run without sudo

# OR run with sudo
sudo python3 main.py
```

### Port already in use

**Error:**
```
Port 8080 is already in use
```

**Solution:**
1. Choose a different port during installation
2. Or stop the conflicting service:
   ```bash
   sudo lsof -i :8080     # Linux — find process
   sudo kill -9 <PID>

   netstat -ano | findstr :8080  # Windows
   taskkill /PID <PID> /F
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
# Delete user database — a new admin with a random password is created on restart
rm ~/.orchix_web_users.json           # Linux
del %USERPROFILE%\.orchix_web_users.json  # Windows
python main.py --web
# Check terminal output for the new admin password
```

### Container won't start

**Check logs:**
```bash
# CLI
python main.py
# Select: Container Management > Select container > View Logs

# Direct Docker
docker logs <container_name>
```

**Common causes:**
- Port conflict → Choose a different port
- Volume permission issue → Run with `sudo` or fix volume permissions
- Missing environment variable → Edit the compose file
- Incompatible DB credentials → Re-install with correct DB connection

### WordPress "Error establishing a database connection"

This means WordPress cannot reach its database. Common causes:

1. **MariaDB not on the orchix network** — restart MariaDB after installing, or run:
   ```bash
   docker network connect orchix mariadb
   ```
2. **Credential mismatch** — the password in `docker-compose-wordpress.yml` differs from MariaDB's. Edit both files to match.
3. **Wrong DB host** — must be the container name (e.g. `mariadb`), not `localhost`.

**Recommended:** Uninstall WordPress and reinstall using the DB discovery feature, which automatically sets the correct host and credentials.

### "No database containers found" warning

This appears when installing apps that need a database (WordPress, phpMyAdmin) and no compatible DB container is running on the orchix network.

**Solution:**
1. Install MariaDB (or PostgreSQL) first via ORCHIX
2. Restart ORCHIX so it connects the new DB to the orchix network
3. Then install WordPress — it will auto-detect the database

---

## Advanced Configuration

### Environment Variables

ORCHIX reads from a `.env` file in the ORCHIX root directory:

```bash
# Web UI
WEB_PORT=5000
WEB_HOST=0.0.0.0

# HTTPS mode (enables Secure cookie flag + HSTS header)
ORCHIX_HTTPS=true

# License
LICENSE_SIGNING_SECRET=your-signing-secret
```

### The Global orchix Network

All ORCHIX containers are connected to the `orchix` Docker network on startup. This enables container-to-container communication by name without exposing additional host ports.

```bash
# View all containers on the orchix network
docker network inspect orchix

# Manually connect an existing container
docker network connect orchix <container_name>

# Verify connectivity (from inside a container)
docker exec wordpress ping mariadb
```

**Compose files** generated by ORCHIX include:
```yaml
networks:
  orchix:
    external: true
```

### Systemd Service (Linux)

Auto-start ORCHIX Web UI on boot:

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
User=root
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
sudo systemctl status orchix
```

### Windows Task Scheduler

Auto-start ORCHIX on boot:

1. Open **Task Scheduler**
2. Create Task:
   - **Name**: ORCHIX
   - **Trigger**: At startup
   - **Action**: Start program
     - Program: `python`
     - Arguments: `C:\orchix\main.py --web --port 5000`
     - Start in: `C:\orchix`
   - **Run with highest privileges**: ✓

### Nginx Reverse Proxy

Expose the ORCHIX Web UI via a domain with HTTPS:

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

        # SSE support (for real-time install/backup progress)
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600;
    }
}
```

Set `ORCHIX_HTTPS=true` in your `.env` file when using HTTPS to enable the Secure cookie flag and HSTS header.

### Docker Resource Limits

Edit a container's `docker-compose-<name>.yml` to limit resources:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Storage Optimization

```bash
# Remove unused Docker images
docker image prune -a

# Remove unused Docker volumes
docker volume prune

# View Docker disk usage
docker system df
```

---

## Support

### Community Support (FREE)

- GitHub Issues: [github.com/Sad-without-you/ORCHIX/issues](https://github.com/Sad-without-you/ORCHIX/issues)
- GitHub Discussions: [github.com/Sad-without-you/ORCHIX/discussions](https://github.com/Sad-without-you/ORCHIX/discussions)

### Priority Support (PRO)

- Email: [support@orchix.dev](mailto:support@orchix.dev)
- Response time: < 24h on weekdays
- Help with: installation, migration, custom templates, performance tuning

### Contact

| | |
|--|--|
| General | [contact@orchix.dev](mailto:contact@orchix.dev) |
| Support | [support@orchix.dev](mailto:support@orchix.dev) |
| Security | [security@orchix.dev](mailto:security@orchix.dev) |

---

## Changelog

### v1.4 (2026-02-27)
- **Self-hosted license server** — Supabase replaced with own secure license server (`/api/v1/validate`)
- **Stripe Checkout + Webhook** — full purchase flow on website: Checkout → Webhook → License generation → n8n email
- **Secure license keys** — HMAC-SHA256 signed (`ORCH-PRO-{16HEX}-{10HMAC}`), only key hash stored in DB, never plaintext
- **Telegram error alerts** — all critical errors (failed payment, email failure, webhook issues) alert owner via n8n → Telegram
- **3-day grace periods** — payment failure grace (server-side) and offline grace (client-side) both set to 3 days
- **Users page security fix** — null-safe `currentUser` check + proper `users.edit` / `users.delete` permission guards on action buttons
- **Nginx Proxy Manager** — access URL now correctly points to Admin UI port (8081) instead of HTTP port (8080)
- **Multi-language website** — DE / EN / GR with automatic browser language detection

### v1.3 (2026-02-20)
- **Global orchix Docker network** — all ORCHIX containers can communicate by container name
- **Dynamic database discovery** — apps that need a DB (WordPress, phpMyAdmin, Adminer) automatically detect running compatible DB containers
- **Auto-fill credentials** — selecting a DB container fills host, user, password, database name, and port automatically
- **db_types filter** — incompatible databases are not shown (e.g. Redis is never offered as a MySQL host)
- **Dynamic placeholder/warning text** — messages reflect the required DB type, not a generic one
- **Port auto-fill** — DB port auto-filled based on detected type (3306 MySQL, 5432 PostgreSQL, etc.)
- **Security fix**: Viewer role can no longer read compose files (which contain database passwords)
- **FREE tier container selection** — when downgrading from PRO, users select which 3 containers to keep managing (Web UI modal + CLI prompt)
- Full multi-volume backup/restore/migration support (Pi-hole, Nginx, InfluxDB, etc.)
- Fixed alpine image lingering after backup/restore/migration operations
- Fixed migration data loss (n8n workflows/accounts preserved across server moves)

### v1.2 (2026-02-14)
- Web UI with modern lily theme (Inter font, pink #ec4899 + teal #14b8a6 design)
- Multi-User RBAC with 3 roles: Admin, Operator, Viewer
- CSRF protection via Flask-WTF
- Security hardening: CSP headers, HSTS, path traversal protection, XSS prevention, thread-safe file ops
- Template system for 30 applications
- Backup & Restore (PRO)
- Server Migration (PRO)
- Audit logging with per-user tracking (PRO)
- Real-time monitoring dashboard with Server-Sent Events (SSE)
- One-click ORCHIX update from Web UI

### v1.1 (2026-01-15)
- Initial public release
- CLI interface with Rich terminal UI
- Basic container management
- 20 application templates

---

**Website:** [orchix.dev](https://orchix.dev)
**GitHub:** [github.com/Sad-without-you/ORCHIX](https://github.com/Sad-without-you/ORCHIX)
**Creator:** [Georgios Sevastakis](https://www.linkedin.com/in/georgios-sevastakis-578a02322/)

© 2026 ORCHIX – All Rights Reserved
