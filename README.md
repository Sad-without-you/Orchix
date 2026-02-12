<p align="center">
  <img src="web/static/favicon.svg" width="80" height="80" alt="ORCHIX">
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
- Modern single-page application with dark theme
- Real-time container status and management
- One-click install, update, uninstall
- YAML editor with syntax highlighting
- Multiple themes (Default, Dracula, Catppuccin, Terminal)
- Grid / List / Compact view modes
- Responsive layout

### CLI
- Interactive terminal interface with Rich formatting
- Live dashboard with CPU, RAM, disk, network monitoring
- Network traffic graph per interface
- Application search and filtering

### Container Management
- One-click deployment with smart port assignment
- Multi-instance support (PRO)
- Automatic conflict detection (name + port)
- Download size display before installation
- Container start / stop / restart / logs / inspect

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
- Session-based authentication with PBKDF2 password hashing
- Rate limiting on login (5 attempts / 5 min)
- Input validation (path traversal, YAML injection, port validation)
- Security headers (X-Frame-Options, CSP, XSS protection)
- Audit logging with full activity trail (PRO)

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

Access at `http://localhost:5000`. A password is generated on first run and displayed in the terminal.

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
│   ├── auth.py             # Authentication
│   ├── api/                # REST API endpoints
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
- Live dashboard
- Web UI
- Install / Update / Uninstall

### PRO Tier - 29 EUR/month
- All 30 applications
- Unlimited containers
- Backup & Restore
- Multi-instance support
- Server migration
- Audit logging
- Priority support

| Feature | FREE | PRO |
|---------|------|-----|
| Applications | All 30 | All 30 |
| Containers | Max 3 | Unlimited |
| Web UI | Yes | Yes |
| Backups | - | Yes |
| Multi-Instance | - | Yes |
| Migration | - | Yes |
| Audit Log | - | Yes |
| Support | Community | Priority |

---

## Security

- PBKDF2 password hashing (upgraded from SHA256)
- Session timeout (8 hours)
- Rate limiting on login
- Input validation on all API endpoints
- Path traversal protection
- YAML injection prevention
- Docker command sanitization
- Security headers on all responses
- Audit logging (PRO)

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
- Delete `~/.orchix_web_password` and restart

---

## Built With

- [Flask](https://flask.palletsprojects.com/) + [Waitress](https://docs.pylonsproject.org/projects/waitress/) - Web server
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Inquirer](https://github.com/magmax/python-inquirer) - Interactive CLI menus
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
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
