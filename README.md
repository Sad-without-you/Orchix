# ORCHIX -  DevOps Container Management 

![ORCHIX Logo](https://img.shields.io/badge/ORCHIX-v1.1-blue)
![License](https://img.shields.io/badge/License-Commercial-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

**Enterprise-grade container management system for deploying, managing, and monitoring containerized applications without Docker expertise.**

Simplify your DevOps workflow with an intuitive CLI interface that handles Docker complexity behind the scenes.

---

## 📌 What is ORCHIX?

ORCHIX is a comprehensive DevOps platform designed to simplify container management for:

- **Small Teams & Startups** - Manage applications without DevOps expertise
- **System Administrators** - Deploy and monitor multiple services efficiently
- **Software Developers** - Focus on code, not infrastructure
- **IT Operators** - Centralized control and backup of all containers

ORCHIX abstracts the complexity of Docker, providing an intuitive interface to install, update, backup, and monitor containerized applications.

---

## 🎯 Key Features

### 🐳 Multi-Application Support (13 Apps)
- **n8n** - Workflow automation engine
- **PostgreSQL** - Enterprise relational database
- **Redis** - High-performance caching & message broker
- **Nginx** - Reverse proxy & load balancing
- **Vaultwarden** - Password manager (Bitwarden-compatible)
- **LightRAG** - AI-powered document analysis
- **Qdrant** - Vector database for AI/ML
- **Grafana** - Metrics visualization & monitoring
- **Jellyfin** - Self-hosted media streaming
- **Nextcloud** - Private cloud storage
- **Stirling-PDF** - PDF manipulation tools
- **More coming soon...**

### 📊 Live Dashboard
- **Real-Time Monitoring** - Auto-refreshing container status every 3s
- **System Health** - CPU, RAM, Disk with visual progress bars
- **Docker Overview** - Engine version, images, volumes, networks
- **Smart Alerts** - Down containers, high CPU/RAM, disk warnings
- **Resource Usage** - Per-container CPU, memory, network I/O

### 📦 Application Management
- **One-Click Installation** - Deploy any app in seconds
- **Multi-Instance Support** - Run multiple instances per app
- **Version Management** - Update with one command
- **Smart Port Assignment** - Automatic port detection
- **Full Uninstall** - Clean removal of all files & data

### 💾 Data Protection (PRO)
- **Automated Backups** - Schedule & manage backups
- **One-Click Restore** - Recover instantly from backups
- **Backup Verification** - Ensure data integrity
- **Complete Cleanup** - Remove all artifacts

### 🔐 Security & Audit (PRO)
- **Audit Logging** - Track all user actions
- **User Activity Tracking** - Know who did what & when
- **Security Monitoring** - Real-time alerts
- **Compliance Ready** - Full audit trail

### 🚀 Advanced Features (PRO)
- **Server Migration** - Move containers between servers
- **Unlimited Containers** - Scale without limits
- **Priority Support** - Fast response times

### 🛠️ System Administration
- **Docker Auto-Install** - Automatic Docker setup
- **System Verification** - Check compatibility
- **WSL2 Configuration** - Windows setup automation
- **Cross-Platform** - Linux & Windows support
- **License Management** - Easy PRO activation

---

## 🎓 Who Should Use ORCHIX?

### ✅ Perfect For:
- **Startups** - Infrastructure without DevOps hires
- **Web Agencies** - Quick multi-client management
- **System Admins** - Centralized container control
- **Developers** - Focus on code, not infrastructure
- **Teams 2-20** - Cost-effective solutions

### ❌ Not For:
- Kubernetes-dependent workflows
- Hyper-scale deployments (100+ containers)
- Custom networking requirements

---

## 📊 Licensing Model

### 🆓 FREE Tier
- **All 13+ applications available**
- 3 containers maximum
- **Live Dashboard** with system health monitoring
- Basic management (install/update/uninstall)
- Community support

### ⭐ PRO Tier - €29/month
- **All 13+ applications available**
- **Unlimited containers**
- **Backup & Restore features**
- **Audit logging (compliance)**
- **Server migration tools**
- **Multi-instance support**
- **Priority email support**

---

## 🚀 Installation

### Prerequisites
- **Linux:** Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 34+, Arch Linux
- **Windows:** Windows 10 (build 19041+) or Windows 11 with WSL2
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended for production)
- **Storage:** 20GB free space
- **Network:** Internet connection for Docker downloads
- **Permissions:** sudo (Linux) or Administrator (Windows)

### Method 1: Manual Installation

**Linux/macOS:**
```bash
# Clone repository
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX

# Install dependencies
pip3 install -r requirements.txt

# Run ORCHIX
sudo python3 main.py
```

**Windows (PowerShell as Administrator):**
```powershell
# Clone repository
git clone https://github.com/Sad-without-you/ORCHIX.git
cd ORCHIX

# Install dependencies
pip install -r requirements.txt

# Run ORCHIX
python main.py
```

### Method 2: Download ZIP

If you don't have Git installed:
1. Download: https://github.com/Sad-without-you/ORCHIX/archive/main.zip
2. Extract the ZIP file
3. Open terminal/PowerShell in the ORCHIX folder
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python main.py` (Windows) or `sudo python3 main.py` (Linux)

### First Run Setup
1. **Launch ORCHIX:** Run the main.py file with appropriate permissions
2. **Install Docker:** Choose "System Setup" → "Install Docker" if not installed
3. **Install Applications:** Navigate to "Install Applications" menu
4. **Select App:** Choose from n8n, PostgreSQL, Redis, Nginx, etc.
5. **Configure:** Set custom port and instance name
6. **Deploy:** Wait for container download and startup
7. **Access:** Open browser to http://localhost:PORT

### Troubleshooting Installation

**Docker not found:**
- Linux: `curl -fsSL https://get.docker.com | sh`
- Windows: Download Docker Desktop from docker.com

**Permission denied:**
- Linux: Ensure you use `sudo`
- Windows: Run PowerShell as Administrator

**Python not found:**
- Install Python 3.8+ from python.org
- Ensure "Add to PATH" is checked during installation

**Module not found errors:**
- Run: `pip install -r requirements.txt --upgrade`

---

## 💻 Detailed Requirements

### Linux
- **OS:** Ubuntu 20.04+, Debian 11+, CentOS 8+
- **CPU:** 2 cores+ recommended
- **RAM:** 4GB+ (8GB for production)
- **Storage:** 20GB+ SSD
- **Privileges:** sudo access
- **Docker:** Auto-installed

### Windows
- **OS:** Windows 10 (19041+) or Windows 11
- **CPU:** 4 cores recommended
- **RAM:** 6GB+ (8GB+ for production)
- **Storage:** 30GB+ (WSL2 space)
- **Privileges:** Administrator
- **Virtualization:** Enabled in BIOS
- **WSL2:** Auto-installed
- **Docker Desktop:** Auto-installed

---

## 📁 Architecture

```
ORCHIX/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── apps/               # Application modules
│   ├── n8n/           # Workflow automation
│   ├── postgres/      # Database
│   ├── redis/         # Cache
│   ├── nginx/         # Web server
│   └── ...
├── cli/                # User interface
│   ├── main_menu.py   # Main menu
│   ├── dashboard.py   # Live monitoring dashboard
│   ├── install_menu.py
│   ├── audit_log_menu.py (PRO)
│   └── ...
├── license/            # License system
│   ├── manager.py
│   └── audit_logger.py (PRO)
├── utils/              # System utilities
├── config/             # Settings
├── audit/              # Audit logs
└── backups/            # Backups
```

---

## 🔧 Configuration

### Default Ports
| App | Port |
|-----|------|
| n8n | 5678 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Nginx | 8080, 8443 |
| Vaultwarden | 8001 |
| Qdrant | 6333 |
| Grafana | 3000 |
| Jellyfin | 8096 |
| Nextcloud | 8090 |
| Stirling-PDF | 8082 |

Custom ports assignable per instance.

---

## 📊 Project Stats

- **8000+** lines of clean Python
- **13+ apps** ready to deploy
- **2 license tiers** (Free & PRO)
- **100% Docker-based** - No VMs needed
- **Easy extension** - Plugin architecture
- **Full audit trail** - Compliance-ready

---

## 🛡️ Security Features

✅ Audit logging with timestamps
✅ License-gated PRO features
✅ Automated backups
✅ Container isolation
✅ User activity tracking
✅ Secure license validation

---

## ⚠️ Important Notes

- **Full Uninstall:** Removes ALL data (irreversible!)
- **Backups:** Essential! Use PRO backups regularly
- **Docker Required:** Auto-installed if missing
- **Permissions:** Linux needs sudo, Windows needs Admin
- **Disk Space:** Monitor for backup storage

---

## 📞 Support & Community

### FREE Tier Support
- 📖 Community documentation
- 🐛 GitHub Issues: Report bugs and request features
- 💬 Community discussions
- 📚 Self-service troubleshooting guides

### PRO Tier Support
- ⚡ Priority email support (24-48h response time)
- 🎯 Direct technical assistance
- 🚀 Fast issue resolution
- 📞 Implementation consultation
- 🔧 Custom configuration help

### Reporting Issues
When reporting issues, please include:
- Operating system and version
- Python version (`python --version`)
- Docker version (`docker --version`)
- Error messages or logs
- Steps to reproduce

---

## 📜 License & Pricing

### Commercial Software
This is proprietary commercial software. See LICENSE file for full terms.

### Pricing Tiers
| Feature | FREE | PRO |
|---------|------|-----|
| **Price** | €0/month | €29/month |
| **Containers** | Max 3 | Unlimited |
| **Applications** | All 13+ apps | All 13+ apps |
| **Backups** | ❌ | ✅ Automated |
| **Multi-Instance** | ❌ | ✅ |
| **Audit Logging** | ❌ | ✅ |
| **Live Dashboard** | ✅ | ✅ |
| **Server Migration** | ❌ | ✅ |
| **Support** | Community | Priority Email |

**Want to try PRO?** Contact us for a demo license key.

---

## 🤝 Contributing

This is commercial software. For bug reports and feature requests, please open a GitHub issue.

For partnership or collaboration inquiries, contact the development team.

---

## 🗺️ Roadmap

### In Development
- 🚧 Backup encryption
- 🚧 Network configuration management
- 🚧 Resource limit controls (CPU/Memory limits)

### Planned Features
- [ ] **Additional Applications** - More pre-configured apps
- [ ] **Automated SSL/TLS** - Let's Encrypt integration
- [ ] **Email Notifications** - Alert system for backups and health
- [x] **Live Dashboard** - Real-time container & system monitoring
- [ ] **Container Health Checks** - Enhanced monitoring
- [ ] **Automatic Updates** - Scheduled container updates
- [ ] **Docker Compose Import** - Import existing compose files
- [ ] **Custom Port Ranges** - Advanced networking options

---

## 📊 Performance & Benchmarks

- **Startup Time:** < 2 seconds
- **Memory Usage:** ~50MB base (excluding containers)
- **CPU Usage:** < 1% when idle
- **Container Deploy Time:** 30-120 seconds (depending on image size)
- **Backup Speed:** ~100MB/s on SSD storage

---

## 🔐 Security & Compliance

- ✅ **Audit Logging:** Complete activity tracking (PRO)
- ✅ **Container Isolation:** Docker security features
- ✅ **No Root Containers:** Rootless mode support
- ✅ **License Validation:** Secure key verification
- ✅ **Data Encryption:** Backup encryption (PRO)
- ✅ **Secure Defaults:** Minimal attack surface

### ⚠️ Important Security Notes

**Backup Security:**
- Backups may contain sensitive data (passwords, encryption keys, API tokens)
- Store backups in secure locations with restricted access
- Consider encrypting backup files before cloud storage
- Never share backup files publicly or with untrusted parties

**Migration Security:**
- Migration packages contain full container configurations
- Review and sanitize before transferring to new systems
- Use secure transfer methods (SSH, encrypted channels)

For security issues, please contact: security@orchix.dev (private disclosure)

---

## 📖 Documentation

- **Quick Start Guide:** See Installation section above
- **User Manual:** Detailed CLI navigation and features
- **Application Guides:** Specific setup for each supported app
- **Troubleshooting:** Common issues and solutions

---

## 🙏 Acknowledgments

Built with:
- **Docker** - Container runtime
- **Python** - Core application logic
- **Rich** - Beautiful terminal UI
- **Inquirer** - Interactive CLI menus
- **PyYAML** - Configuration management

---

**ORCHIX: Simplifying DevOps for Everyone**

🌐 **Links:**
- GitHub: https://github.com/Sad-without-you/ORCHIX
- Issues: https://github.com/Sad-without-you/ORCHIX/issues
- Discussions: https://github.com/Sad-without-you/ORCHIX/discussions

📧 **Contact:**
- General: contact@orchix.dev
- Support: support@orchix.dev
- Security: security@orchix.dev

👤 **Creator:**
- LinkedIn: [Georgios Sevastakis](https://www.linkedin.com/in/georgios-sevastakis-578a02322/)

---

*Made with ❤️ for developers who want to focus on building, not configuring.*
