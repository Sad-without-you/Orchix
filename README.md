<p align="center">
  <img src="web/static/favicon.svg?v=1.2" width="80" height="80" alt="ORCHIX">
</p>

<h1 align="center">ORCHIX</h1>
<p align="center"><strong>DevOps Container Management System</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/ORCHIX-v1.2-14b8a6" alt="Version">
  <img src="https://img.shields.io/badge/License-Commercial-brightgreen" alt="License">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-blue" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Apps-30-14b8a6" alt="Apps">
</p>

<p align="center">
  Deploy, manage, and monitor containerized applications without Docker expertise.<br>
  CLI + Web UI with built-in backup, migration, and audit logging.
</p>

---

## What is ORCHIX?

ORCHIX is a container management platform that abstracts Docker complexity behind an intuitive interface. It includes a full-featured CLI and a modern Web UI, both capable of installing, updating, and monitoring 30 pre-configured applications.

**Target users:**
- Small teams and startups without dedicated DevOps
- System administrators managing multiple services
- Developers who want to focus on code, not infrastructure

---

## Key Features

### 30 Pre-Configured Applications

| Category | Applications |
|----------|-------------|
| **Web & CMS** | WordPress, Nextcloud, Nginx Proxy Manager |
| **Databases** | PostgreSQL, MariaDB, Redis, InfluxDB, Qdrant |
| **DevOps** | n8n, Gitea, Traefik, Watchtower, Dozzle |
| **Monitoring** | Grafana, Uptime Kuma, Changedetection.io |
| **Security** | Vaultwarden, Pi-hole |
| **Media** | Jellyfin, Stirling PDF, File Browser |
| **Tools** | Adminer, phpMyAdmin, IT-Tools, Homer, Homarr, Heimdall, Duplicati, MinIO, Eclipse Mosquitto |

### Web UI
- Modern single-page application with lily theme (pink #ec4899 + teal #14b8a6)
- **Multi-User with Role-Based Access Control (RBAC)**: Admin, Operator, Viewer
- Real-time container status via Server-Sent Events (SSE)
- One-click install, update, uninstall
- YAML editor with syntax highlighting
- Live system monitoring dashboard (CPU, RAM, disk, network)
- User management panel (Admin only)
- Responsive layout with sidebar collapse
- Inter font for better readability

### CLI
- Interactive terminal interface with Rich formatting
- Live dashboard with real-time metrics (CPU, RAM, disk, network)
- Network traffic graph per interface with upload/download rates
- Docker container monitoring with status indicators
- Application search and filtering with category browsing

### Container Management
- One-click deployment with smart port assignment
- Multi-instance support (PRO)
- Automatic conflict detection (name + port)
- Docker image size display before installation (MB/GB)
- Container operations: start, stop, restart, logs, inspect, delete
- Real-time container status updates
- Volume and network management

### Data Protection (PRO)
- Automated backup per application
- One-click restore
- Backup verification and metadata
- Cross-platform backup format (Linux / Windows)

### Server Migration (PRO)
- Export migration packages with backups + compose files
- Import on target server with automatic deployment
- Platform-aware packaging (tar.gz / zip)

### Security
- **Multi-User Authentication** with RBAC (Admin / Operator / Viewer)
- PBKDF2-SHA256 password hashing (Werkzeug)
- CSRF protection (Flask-WTF double-submit cookie)
- Rate limiting on login (5 attempts / 5 min)
- Input validation on all endpoints (path traversal, YAML injection, port validation)
- Security headers (Content-Security-Policy, X-Frame-Options, HSTS, X-Content-Type-Options)
- Docker command sanitization to prevent command injection
- Thread-safe file operations with atomic writes
- Tarball path traversal protection on migration import
- XSS prevention with output escaping
- Audit logging with per-user activity trail (PRO)

### System
- Docker auto-installation (Linux + Windows/WSL2)
- Update check from GitHub
- System requirements verification
- Cross-platform: Linux and Windows

---

## Installation

### Prerequisites

- **Python** 3.8+
- **Docker** (auto-installed via setup menu if missing)
- **RAM** 4 GB minimum (8 GB recommended)
- **Storage** 20 GB free
- **OS** Ubuntu 20.04+, Debian 11+, Windows 10/11 with WSL2

### Quick Start

**Linux:**
```bash
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX
pip3 install -r requirements.txt
sudo python3 main.py
```

**Windows (PowerShell as Administrator):**
```powershell
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX
pip install -r requirements.txt
python main.py
```

### Web UI Mode

```bash
python main.py --web              # Default port 5000
python main.py --web --port 8080  # Custom port
```

Access at `http://localhost:5000`. An admin user with a random password is created on first run and displayed in the terminal. Log in with username `admin`.

### First Run

1. Launch ORCHIX (CLI or Web)
2. System Setup > Install Docker (if needed)
3. Install Applications > Select app > Configure port > Deploy
4. Access at `http://localhost:PORT`

---

## Architecture

```
ORCHIX/
├── main.py                 # Entry point (CLI + Web)
├── requirements.txt        # Python dependencies
├── apps/
│   ├── templates.json      # All 30 app definitions
│   ├── template_installer.py
│   ├── template_updater.py
│   ├── manifest_loader.py
│   └── hook_loader.py      # Backup/restore/ready hooks
├── cli/
│   ├── main_menu.py
│   ├── dashboard.py        # Live terminal dashboard
│   ├── install_menu.py
│   ├── container_menu.py
│   └── ...
├── web/
│   ├── server.py           # Flask + Waitress
│   ├── auth.py             # Multi-User Auth + RBAC
│   ├── api/                # REST API endpoints
│   │   └── users.py        # User management (Admin)
│   ├── static/             # CSS, JS, favicon
│   └── templates/          # HTML templates
├── license/
│   ├── manager.py          # License management
│   ├── secure_license.py   # Key validation
│   └── audit_logger.py     # Audit logging (PRO)
├── utils/
│   ├── validation.py       # Input sanitization
│   ├── version_check.py    # GitHub update check
│   ├── docker_utils.py     # Safe Docker execution
│   └── system.py           # OS detection, Docker install
└── config/
```

---

## Default Ports

| Application | Default Port |
|------------|-------------|
| n8n | 5678 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Nginx Proxy Manager | 8080, 8443, 81 |
| Vaultwarden | 8001 |
| Grafana | 3000 |
| Jellyfin | 8096 |
| Nextcloud | 8090 |
| WordPress | 8080 |
| Gitea | 3001 |
| Uptime Kuma | 3002 |
| Stirling PDF | 8082 |

All ports are configurable during installation.

---

## Licensing

### FREE Tier
- All 30 applications
- Up to 3 containers
- 1 user (single admin)
- Live dashboard (CLI + Web UI)
- Container management (install/update/uninstall/logs)
- Real-time monitoring
- Community support

### PRO Tier - €29/month
- All 30 applications
- Unlimited containers
- **Multi-User** with RBAC (Max 3: Admin, Operator, Viewer)
- Automated backup & restore
- Multi-instance support
- Server migration tools
- Audit logging with per-user activity trail
- Priority email support

| Feature | FREE | PRO |
|---------|------|-----|
| Applications | All 30 | All 30 |
| Containers | Max 3 (selectable) | Unlimited |
| Users | 1 | Max 3 |
| RBAC Roles | — | Admin, Operator, Viewer |
| Web UI + CLI | ✓ | ✓ |
| Real-time Monitoring | ✓ | ✓ |
| Backups | — | ✓ |
| Multi-Instance | — | ✓ |
| Migration | — | ✓ |
| Audit Log | — | ✓ |
| Support | Community | Priority |

---

## Security

- **Multi-User RBAC** with backend permission enforcement (Admin / Operator / Viewer)
- PBKDF2-SHA256 password hashing (Werkzeug, 100k+ iterations)
- **CSRF protection** via Flask-WTF (double-submit cookie pattern)
- Session timeout (8 hours) with secure cookie flags
- Rate limiting on login (5 attempts / 5 min per IP)
- Input validation on all API endpoints
- Path traversal protection (filesystem + tarball extraction)
- YAML injection prevention (`yaml.safe_load()`)
- Docker command sanitization (subprocess with list args, no shell)
- Security headers: Content-Security-Policy, X-Frame-Options, HSTS, X-Content-Type-Options
- XSS prevention with HTML output escaping
- Thread-safe file operations with atomic writes and file permission hardening
- Audit logging with per-user tracking (PRO)

For security issues: security@orchix.dev

---

## Troubleshooting

**Docker not found:**
- Linux: `curl -fsSL https://get.docker.com | sh`
- Windows: Install Docker Desktop, enable WSL2

**Permission denied:**
- Linux: `sudo python3 main.py` or add user to docker group
- Windows: Run PowerShell as Administrator

**Module not found:**
- `pip install -r requirements.txt --upgrade`

**Web UI password reset:**
- Delete `~/.orchix_web_users.json` and restart (a new admin user with random password will be created)

---

## Built With

- [Flask](https://flask.palletsprojects.com/) 3.0+ - Web framework
- [Flask-WTF](https://flask-wtf.readthedocs.io/) 1.2+ - CSRF protection
- [Waitress](https://docs.pylonsproject.org/projects/waitress/) 3.0+ - Production WSGI server
- [Rich](https://github.com/Textualize/rich) 13.7+ - Terminal UI with colors and tables
- [Inquirer](https://github.com/magmax/python-inquirer) 3.1+ - Interactive CLI menus
- [psutil](https://github.com/giampaolo/psutil) 5.9+ - System and process monitoring
- [PyYAML](https://pyyaml.org/) 6.0+ - YAML configuration parsing
- [Requests](https://requests.readthedocs.io/) 2.31+ - HTTP client for license validation
- [python-dotenv](https://github.com/theskumar/python-dotenv) 1.0+ - Environment variable management
- [Docker](https://www.docker.com/) - Container runtime

---

## Links

- GitHub: https://github.com/Sad-without-you/ORCHIX
- Issues: https://github.com/Sad-without-you/ORCHIX/issues

## Contact

- General: contact@orchix.dev
- Support: support@orchix.dev
- Security: security@orchix.dev

## Creator

[Georgios Sevastakis](https://www.linkedin.com/in/georgios-sevastakis-578a02322/)
