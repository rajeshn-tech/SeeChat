# SeeChat Studio Communication Suite – Maintenance & Operations Guide

## 1. Directory Structure & File Integrity
```text
SeeChat/
├── client/                     # Frontend static assets (app.js, index.html, styles.css)
├── database/                   # SQLite database access layers & schema migrations
├── data/                       # Active SQLite WAL database storage (seechat_audit.db)
├── logs/                       # Application runtime error logs directory
├── chat_logs/                  # Compliance CSV audit logs directory
├── services/                   # Business logic, JWT auth & CSV formula sanitization
├── socket_handlers/            # Real-time modular Socket.IO event handlers
├── tests/                      # Automated test suite (test_seechat.py - 37 unit tests)
├── config.py                   # Central server configuration settings
├── server.py                   # Flask-SocketIO entry point (Port 8080)
├── https_setup.py              # TLS/SSL certificate setup utility
├── auto_run_server.py          # Watchdog daemon script with crash-loop recovery
├── reset_db.py                 # Emergency development password reset tool
├── launch-server.bat           # Windows launch batch script
└── requirements.txt            # Production Python dependencies
```

## 2. HTTPS & TLS Certificate Management
TLS certificate preparation is consolidated into `https_setup.py`:

```bash
python https_setup.py
```

### Safety Rules:
- `cert.pem` (Public Certificate) and `key.pem` (Private Key) remain separate generated files.
- Existing certificates are **NEVER overwritten automatically** if present.
- Both `cert.pem` and `key.pem` are strictly excluded from version control via `.gitignore`.
- Development self-signed certificates are generated for local LAN testing (`localhost`, `127.0.0.1`, `seechat`). Trusted studio CA certificates will be installed during final deployment.

## 3. Server Startup & Watchdog Management

### Normal Direct Startup:
```bash
python server.py
```

### Watchdog Production Daemon (Auto-Restart):
```bash
python auto_run_server.py
```
- Monitors `server.py` process.
- Automatically restarts server upon unexpected termination.
- Includes CPU spin-loop prevention (pauses 5 seconds if 3 rapid crashes occur in <2 seconds).

## 4. Emergency Database & Recovery Tool (`reset_db.py`)
`reset_db.py` is a development password reset utility used to clear password hashes (`UPDATE users SET password_hash = ''`) during local testing.

### Safety Guard:
- Requires interactive prompt confirmation (`CONFIRM`) or non-interactive environment flag `SEECHAT_ALLOW_DB_RESET=true` / `--force`.

## 5. Active Directory Integration Phasing
Active Directory LDAP authentication is currently disabled for local development (`AD_AUTH_ENABLED = False`). 

### Production Enablement:
1. Update `config.py` or set environment variable `AD_AUTH_ENABLED=true`.
2. Configure `AD_LDAP_SERVER` (e.g. `ldaps://192.168.1.100`) and `AD_DOMAIN` (e.g. `STUDIO`).

## 6. Automated Testing & Verification
Run the complete automated unit test suite before pushing changes:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
Baseline: **37/37 Tests Passed (100%)**.
