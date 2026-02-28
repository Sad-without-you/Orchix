# ORCHIX Changelog

## v1.5 (in progress)

### New Commands
- **`orchix reset-password`** — resets the admin password when no user has ever logged in; safely refuses (with a clear message) if anyone has already authenticated; generates and displays a new random password in the credentials box

### Bug Fixes
- **Config directory inconsistency fixed** — `orchix_configs` (no dot) and `.orchix_configs` (with dot) were used inconsistently across components; now unified to `~/.orchix_configs/` everywhere
- **Uninstaller: folder now fully deleted** — fixed CWD lock issue on Windows (`Set-Location $env:TEMP` before `rd /s /q`); switched from PS temp-script to `cmd.exe` approach (no execution policy issues)
- **Uninstaller: reliable script dir detection** — added `$PSScriptRoot`, `$PSCommandPath`, `$MyInvocation`, and `$PWD` fallbacks so `$ScriptDir` is never empty
- **Uninstaller: path display** — fixed blank path in prompts by using `Write-Host` for path display instead of embedding in `Read-Host` string
- **Uninstaller: `$pid` reserved variable** — replaced with `$orchixPid` + `Stop-Process` to avoid shadowing PowerShell's built-in `$pid`
- **install.ps1: UTF-8 BOM removed** — BOM broke `irm | iex` with `Die Benennung "﻿#" wurde nicht erkannt`; `uninstall.ps1` keeps BOM (run from disk only)
- **License URL** — fixed `orchix.dev/pricing` → `orchix.dev/#pricing` in CLI menus
- **License expiry parsing** — hardened `datetime.fromisoformat()` with try/except to prevent crash on unexpected server response format
- **Credentials box alignment** — padding now calculated from plain text length (not ANSI-escaped string)
- **install.sh: `curl | bash` stdin fix** — replaced unreliable `exec </dev/tty` approach with a full self-re-exec guard: the script saves itself to a temp file and re-execs with `/dev/tty` as stdin, making all interactive prompts work reliably on all Linux distros including Raspberry Pi; all Python subprocess calls also receive `</dev/null` to prevent pipe-byte consumption
- **install.sh: Docker daemon auto-start** — if Docker is installed but the daemon is not running, the installer now automatically runs `sudo systemctl start docker` (falls back to `sudo service docker start`) before prompting to start the service
- **install.sh: docker group auto-add** — if the current user is not in the `docker` group, the installer runs `sudo usermod -aG docker $USER` and uses `sg docker` when starting the ORCHIX service, so no logout/login is required
- **install.sh: global symlink with sudo fallback** — when `/usr/local/bin` is not directly writable, the installer now retries with `sudo ln -sf`, so `orchix` becomes available globally without manual steps
- **install.sh: absolute path in orchix.sh launcher** — `$INSTALL_DIR` is now embedded at install time into the heredoc rather than resolved at runtime, fixing `No such file or directory` when `orchix` is symlinked to `/usr/local/bin`
- **install.sh: input buffer flush** — added `read -r -t 0.1 -n 10000 _flush` between the two interactive prompts to prevent a leftover Enter keypress from auto-answering the second prompt
- **apps/manifest_loader.py: relative path fix** — changed `Path('apps') / 'templates.json'` to `Path(__file__).parent / 'templates.json'`; fixes the empty Applications page when systemd starts the service with a working directory other than the ORCHIX root
- **cli/service_manager.py: systemd WorkingDirectory** — added `WorkingDirectory=<INSTALL_DIR>` to the generated systemd unit file; ensures all relative paths inside the service resolve correctly
- **cli/service_manager.py: sg docker wrapper** — the systemd service now executes through a `.orchix_launcher.sh` wrapper that applies `sg docker` so the web process always has Docker socket access even when the user was just added to the docker group
- **utils/system.py: docker info with timeout** — changed `docker version` to `docker info` with `timeout=5`; fixes Docker Engine showing as "Stopped" in the dashboard when the daemon is running but slow to respond

### Documentation
- **README.md**: fixed 6 wrong default ports, added `service uninstall` command, simplified run commands to plain `orchix` / `orchix --web`, fixed password reset path, added `orchix reset-password` command
- **DOCUMENTATION.md**: full overhaul — fixed platform info, CLI launch commands, Web UI commands, password reset paths, removed outdated `pip install` troubleshooting, replaced wrong Systemd/Task Scheduler sections with correct `orchix service enable/disable`, corrected Environment Variables section (removed non-existent `WEB_PORT`/`WEB_HOST`/`LICENSE_SIGNING_SECRET`), added `orchix reset-password` command
- **CHANGELOG.md**: extracted from `DOCUMENTATION.md` into its own file

---

## v1.4 (2026-02-27)
- **Self-hosted license server** — Supabase replaced with own secure license server (`/api/v1/validate`)
- **Stripe Checkout + Webhook** — full purchase flow on website: Checkout → Webhook → License generation → n8n email
- **Secure license keys** — HMAC-SHA256 signed (`ORCH-PRO-{16HEX}-{10HMAC}`), only key hash stored in DB, never plaintext
- **Telegram error alerts** — all critical errors (failed payment, email failure, webhook issues) alert owner via n8n → Telegram
- **3-day grace periods** — payment failure grace (server-side) and offline grace (client-side) both set to 3 days
- **Users page security fix** — null-safe `currentUser` check + proper `users.edit` / `users.delete` permission guards on action buttons
- **Nginx Proxy Manager** — access URL now correctly points to Admin UI port (8081) instead of HTTP port (8080)
- **Multi-language website** — DE / EN / GR with automatic browser language detection

## v1.3 (2026-02-20)
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

## v1.2 (2026-02-14)
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

## v1.1 (2026-01-15)
- Initial public release
- CLI interface with Rich terminal UI
- Basic container management
- 20 application templates
