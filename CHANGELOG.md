# ORCHIX Changelog

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
