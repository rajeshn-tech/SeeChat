# 📘 SeeChat Developer & Maintenance Guide

**Target Audience**: Beginner & Intermediate Python Developers  
**Application**: SeeChat Studio Communication Suite  
**Project Location**: `C:\Users\rajeshn\Desktop\Rajesh\Desk Ping`  
**Internal Port**: `8080` (Preserved)  
**Authentication Mode**: Development Token Auth (`AD_AUTH_ENABLED = False`)  

---

## 1. Project Overview

**SeeChat** is a browser-based internal office messenger designed for studio environments (VFX, Animation, Game Development, IT Studios). It enables real-time 1-to-1 direct messaging, broadcast group messaging, and studio-wide administrative announcements across LAN workstations.

SeeChat is engineered to be **lightweight, secure, beginner-friendly, and easy to maintain** without complex enterprise frameworks.

---

## 2. Architecture Overview

### High-Level Data Flow

```text
Browser Client (HTML / JS / CSS)
       │
       ▼  HTTP & WebSockets (Port 8080)
Flask WSGI Application Gateway (server.py)
       │
       ├── Real-time Socket Event Handlers (socket_handlers/)
       │       │
       │       ▼
       ├── Security & Business Logic (services/)
       │       │
       │       ▼
       └── Database Data Layer (database/)
               │
               ▼
       SQLite WAL Engine (Dev) / PostgreSQL (Prod)
```

### Architectural Layer Responsibilities
* **Client Layer (`client/`)**: HTML5 shell (`index.html`), Catppuccin Dark Slate CSS (`styles.css`), browser-controlled popup window (`popup.html`), and Socket.IO client logic (`app.js`).
* **Gateway Layer (`server.py`)**: Flask WSGI application host running Gevent async coroutine engine on internal port `8080`.
* **Event Handlers Layer (`socket_handlers/`)**: Dispatches real-time Socket.IO events for connection, messaging, chat requests, presence, and group management.
* **Services Layer (`services/`)**: Enforces authentication (`auth_service.py`), chat relationship authorization (`chat_request_service.py`), payload length validation & text-only enforcement (`chat_service.py`), and CSV audit logging with formula injection protection (`audit_service.py`).
* **Database Layer (`database/`)**: Manages database connection pooling (`db.py`), user profiles (`users.py`), message storage (`messages.py`), chat request states (`chat_requests.py`), and broadcast groups (`groups.py`).

---

## 3. Project Folder Structure

```text
C:\Users\rajeshn\Desktop\Rajesh\Desk Ping\
├── .gitignore                      → Git tracking exclusion rules for pycache, compiled files, and private keys
├── HOW_TO_CHANGE_FEATURES.md       → Quick beginner feature modification cheat sheet
├── PROJECT_ARCHITECTURE.md         → Architectural system map and security data flow rules
├── SEECHAT_DEVELOPER_GUIDE.md      → Master developer & maintenance guide (This Document)
├── auto_run_server.py              → Service watchdog daemon with rapid crash-loop recovery protection
├── cert.pem                        → Development TLS SSL public certificate
├── config.py                       → Centralized application configuration settings (Port 8080, limits, AD toggle)
├── generate_ssl.py                 → Self-signed RSA SSL certificate generation utility
├── key.pem                         → Development TLS SSL private key
├── launch-server.bat               → One-click Windows batch script launcher for non-technical users
├── requirements-dev.txt            → Developer testing & resource monitoring dependencies (psutil, websocket-client)
├── requirements.txt                → Core production runtime dependencies (Flask, Flask-SocketIO, PyJWT, gevent)
├── reset_db.py                     → Database reset & password hash helper script (Safety Guarded)
├── server.py                       → Modular application entry point & Socket.IO server host (Port 8080)
├── server_setup_guide.md           → Dedicated production deployment guide for Nginx, HTTPS, AD & PostgreSQL
├── users.json                      → Default user seed list & role configuration template
│
├── database/                       → Database Persistence Layer
│   ├── __init__.py                 → Package marker
│   ├── db.py                       → Dynamic PostgreSQL / SQLite WAL connection manager
│   ├── users.py                    → User profile queries, roles, and status updates
│   ├── messages.py                 → Parameterized message storage and chat history retrieval
│   ├── chat_requests.py            → User relationship authorization state queries
│   └── groups.py                   → Broadcast group membership & management queries
│
├── services/                       → Business Logic Layer
│   ├── __init__.py                 → Package marker
│   ├── ad_service.py               → Active Directory / LDAP authentication verification stub
│   ├── audit_service.py            → Compliance CSV audit logging & formula injection protection
│   ├── auth_service.py             → Cryptographic JWT token signing & session authentication
│   ├── chat_request_service.py     → Backend relationship authorization validation
│   └── chat_service.py             → Direct message validation & text-only enforcement
│
├── socket_handlers/               → Real-Time Socket.IO Event Handlers
│   ├── __init__.py                 → Package marker
│   ├── connection.py               → Authentication & debounced presence broadcast event handlers
│   ├── messages.py                 → Direct/broadcast message dispatching & rate limiting handlers
│   ├── chat_requests.py            → Chat request sending, response, and status event handlers
│   ├── presence.py                 → User online/offline status event handlers
│   └── groups.py                   → Group creation, rename, delete, and admin event handlers
│
├── tests/                          → Automated Test Harness
│   ├── __init__.py                 → Package marker
│   ├── load_test.py                → High-concurrency progressive Socket.IO load test script
│   └── test_seechat.py             → Comprehensive 26-case automated security unit test suite
│
├── client/                         → Visual Application Layer (Visually Locked)
│   ├── index.html                  → Main messenger UI shell & IT Admin panel
│   ├── popup.html                  → Browser-controlled popup window alert shell
│   ├── app.js                      → Client Application logic, DOM handling, & Socket.IO client
│   ├── presentation.html           → Executive presentation deck viewer
│   └── styles.css                  → Modern Catppuccin Dark Slate styling rules
│
└── data/                           → Local Database Storage
    └── seechat_audit.db            → Active SQLite WAL database file
```

---

## 4. Feature → File → Function Map

| Feature / Setting | Target File | Function / Setting Name | Risk Level | What To Test After Editing |
| :--- | :--- | :--- | :--- | :--- |
| **Server Port** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `PORT = 8080` | **SAFE** | `python server.py` startup & login |
| **Server Binding Host** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `HOST = '0.0.0.0'` | **SAFE** | LAN workstation connection |
| **Active Directory Toggle**| [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `AD_AUTH_ENABLED` | **CAUTION** | Test login with domain credentials |
| **Database Engine Switch**| [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `DATABASE_URL` / `DB_TYPE` | **EXPERT** | Check table creation & connection |
| **Message Max Length** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `MESSAGE_MAX_LENGTH = 2000` | **SAFE** | Run `test_12_oversized_message_blocked` |
| **Message Rate Limit** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `MAX_MESSAGES_PER_SECOND = 10` | **SAFE** | Run `test_23_message_rate_limiting` |
| **Admin Direct Msg Bypass**| [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `ADMIN_DIRECT_MESSAGE = True` | **SAFE** | Run `test_10` & `test_11` |
| **Text-Only Enforcement** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | `ALLOW_FILE_SHARING = False` | **EXPERT** | Run `test_16_file_upload_disabled` |
| **Login Authentication** | [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py) | `authenticate_user()` | **CAUTION** | Run `test_01`, `test_02`, `test_03` |
| **JWT Expiry & Secret** | [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py) | `generate_jwt_token()` | **CAUTION** | Run `test_15_jwt_token_validation_and_tampering` |
| **User Profile & Roles** | [`database/users.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/users.py) | `get_user_by_username()` | **CAUTION** | Run `test_03` & `test_19` |
| **Disable / Enable User** | [`database/users.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/users.py) | `toggle_user_disabled()` | **CAUTION** | Run `test_03_disabled_user_login_blocked` |
| **Direct Messaging** | [`services/chat_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/chat_service.py) | `process_direct_message()` | **CAUTION** | Run `test_04` through `test_07` |
| **Chat Requests** | [`services/chat_request_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/chat_request_service.py)| `is_chat_allowed()` | **EXPERT** | Run `test_04` through `test_09` |
| **Groups & Broadcast** | [`database/groups.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/groups.py) | `create_broadcast_group()` | **SAFE** | Run `test_20` & `test_26` |
| **Notifications & Popups** | [`client/app.js`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/app.js) | `openDesktopFloatingPopupWindow`| **SAFE** | Test popup notification in Chrome |
| **Presence Broadcast** | [`socket_handlers/connection.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/connection.py)| `broadcast_online_users()` | **CAUTION** | Test presence update in browser |
| **Audit CSV Logging** | [`services/audit_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/audit_service.py) | `sanitize_csv_field()` | **CAUTION** | Run `test_17`, `test_22`, `test_25` |
| **Database Reset Guard** | [`reset_db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/reset_db.py) | `confirm_reset()` | **CAUTION** | Run `test_24_reset_db_safety_guard_rejection` |
| **Watchdog Auto-Restart** | [`auto_run_server.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/auto_run_server.py) | `run_auto_self_server()` | **SAFE** | Test server crash recovery loop |
| **Server Startup Entry** | [`server.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/server.py) | `socketio.run(app)` | **CAUTION** | Run `python server.py` manually |
| **UI Aesthetics & Shell** | [`client/index.html`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/index.html) / [`styles.css`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/styles.css) | HTML / CSS markup | **CAUTION (Locked)**| Visually verify UI layout in Chrome |

---

## 5. Safe Editing Guide

Files are categorized into three risk levels to guide developers:

### 🟢 SAFE TO EDIT
These files control configuration defaults, utility scripts, presentation pages, or tests. Modifying them carries minimal risk of breaking server runtime logic:
* [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py)
* [`auto_run_server.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/auto_run_server.py)
* [`users.json`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/users.json)
* [`launch-server.bat`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/launch-server.bat)
* [`generate_ssl.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/generate_ssl.py)
* [`client/presentation.html`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/presentation.html)
* [`socket_handlers/presence.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/presence.py)
* [`tests/test_seechat.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/tests/test_seechat.py)

### 🟡 CAUTION REQUIRED
These files contain core event handlers, client rendering logic, or database CRUD helpers. Edit carefully and run automated unit tests after changes:
* [`server.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/server.py)
* [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py)
* [`services/chat_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/chat_service.py)
* [`services/audit_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/audit_service.py)
* [`services/ad_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/ad_service.py)
* [`database/users.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/users.py)
* [`database/messages.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/messages.py)
* [`database/groups.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/groups.py)
* [`socket_handlers/connection.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/connection.py)
* [`socket_handlers/messages.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/messages.py)
* [`socket_handlers/chat_requests.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/chat_requests.py)
* [`socket_handlers/groups.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/socket_handlers/groups.py)
* [`client/app.js`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/app.js)
* [`client/index.html`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/index.html) *(Visually Locked)*
* [`client/styles.css`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/styles.css) *(Visually Locked)*
* [`client/popup.html`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/popup.html) *(Visually Locked)*
* [`reset_db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/reset_db.py)

### 🔴 EXPERT / SECURITY SENSITIVE
These files control system security, connection pooling, schema initialization, or backend permission enforcement. Edit only when authorized:
* [`database/db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/db.py)
* [`services/chat_request_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/chat_request_service.py)

---

## 6. Important Configuration Settings

All central settings reside in [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py):

```python
APP_NAME = "SeeChat"
BRANDING_NAME = "SeeChat Studio Communication Suite"

# SERVER NETWORK & PORT CONFIGURATION
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 8080))
CUSTOM_HOST = os.environ.get('SEECHAT_HOST', 'seechat')
USE_SSL = os.environ.get('USE_SSL', 'false').lower() == 'true'

# SECRET KEY & JWT CONFIGURATION (HS256 Token Signing)
SECRET_KEY = os.environ.get('SEECHAT_SECRET_KEY', 'seechat_lan_enterprise_jwt_secret_2026_hs256')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_SECONDS = 86400 * 30  # 30 Days

# CHAT PERMISSION & SECURITY RULES
CHAT_REQUEST_REQUIRED = True
ADMIN_DIRECT_MESSAGE = True  # Admin bypass for IT operational communications
MESSAGE_MAX_LENGTH = 2000
ALLOW_FILE_SHARING = False   # Strictly Text-Only Messaging (Zero Upload Endpoints)

# ACTIVE DIRECTORY (AD / LDAP) CONFIGURATION PHASING
AD_AUTH_ENABLED = os.environ.get('AD_AUTH_ENABLED', 'false').lower() == 'true'
AD_LDAP_SERVER = os.environ.get('AD_LDAP_SERVER', 'ldaps://192.168.1.100')
AD_DOMAIN = os.environ.get('AD_DOMAIN', 'STUDIO')

# DATABASE ENGINE CONFIGURATION
DATABASE_URL = os.environ.get('DATABASE_URL', '')
DATABASE_TYPE = os.environ.get('DB_TYPE', 'postgresql' if DATABASE_URL else 'sqlite')

# AUDIT & COMPLIANCE LOGGING
AUDIT_LOGGING = True
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
CHAT_LOGS_DIR = os.path.join(os.path.dirname(__file__), 'chat_logs')
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'users.json')

# RATE LIMITING THRESHOLDS
MAX_LOGIN_ATTEMPTS = 5
MAX_MESSAGES_PER_SECOND = 10
```

---

## 7. Login Flow

```text
Browser User submits login form in client/app.js
       ↓
Client emits Socket.IO event 'user_login' { username, password }
       ↓
socket_handlers/connection.py -> handle_login(data)
       ├── If data has 'token': verify_jwt_token(token) via services/auth_service.py
       └── If data has 'username': authenticate_user(username, password, ip)
               ├── If AD_AUTH_ENABLED == True  -> verify via services/ad_service.py (LDAP)
               └── If AD_AUTH_ENABLED == False -> verify via database/users.py (Dev mode)
       ↓
If valid -> generate_jwt_token(username, role)
       ↓
Server emits 'login_success' with { username, role, token }
       ↓
Client stores token in localStorage and unlocks main UI shell
```

---

## 8. Message Flow

```text
Sender clicks 'Send' in client/app.js
       ↓
Client emits Socket.IO event 'send_direct_message'
       ↓
socket_handlers/messages.py -> handle_direct_message(data)
       ↓
Check rate limit -> is_rate_limited(sender) (Max 10 msgs/sec)
       ↓
services/chat_service.py -> process_direct_message()
       ├── Check text length (Max 2000 chars)
       └── Check chat relationship -> services/chat_request_service.is_chat_allowed()
               ├── If PENDING / REJECTED / NONE -> BLOCKED BY SERVER
               └── If ACCEPTED (or Admin)      -> ALLOWED
       ↓
Save to database -> database/messages.save_message()
       ↓
Write compliance CSV log -> services/audit_service.append_to_chat_csv() (Sanitizes formula injection)
       ↓
Server emits 'message_sent_confirm' to Sender & 'receive_direct_message' to Recipient socket room
```

---

## 9. Security-Critical Rules & Current Known Warnings

### Security Rules
1. **Never Bypass Backend Chat Authorization**: `services/chat_service.py` must ALWAYS execute `is_chat_allowed()` on the server. Never rely on client UI flags.
2. **Never Trust Client Role**: Server handlers must look up the user's role from the database or verified JWT token.
3. **Zero AD Password Storage**: Active Directory passwords must never be stored in DB, CSV, browser storage, or logs.
4. **Strict Text-Only Enforcement**: `config.ALLOW_FILE_SHARING = False`. Never expose upload endpoints.
5. **Preserve SQL Parameterization**: Always use parameterized placeholders (`?` for SQLite, `%s` for PostgreSQL) to prevent SQL injection.
6. **Preserve XSS Escaping**: Always apply `escapeHtml()` in `client/app.js` before inserting user content into the DOM.

### Current Known Warnings
1. **Development Fallback Secret Key**: In development mode, `SECRET_KEY` uses a default string if `SEECHAT_SECRET_KEY` is not set. Production deployments must export `SEECHAT_SECRET_KEY` in environment variables.
2. **Development Seed Accounts**: When `AD_AUTH_ENABLED = False`, default workstation accounts allow passwordless login. Setting `AD_AUTH_ENABLED = True` forces LDAP domain authentication.
3. **LocalStorage Token Storage**: JWT tokens stored in `localStorage` rely on strict DOM HTML escaping (`escapeHtml()`) for XSS protection.

---

## 10. Testing After Modification

The current automated test suite ([`tests/test_seechat.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/tests/test_seechat.py)) contains **26 automated test cases**:

### Feature Modification Test Mapping

| Feature Area Changed | Associated Test Cases |
| :--- | :--- |
| **Development Authentication** | `test_01_valid_development_login`, `test_02_invalid_development_login` |
| **Disabled User Account** | `test_03_disabled_user_login_blocked` |
| **Chat Request Authorization** | `test_04`, `test_05`, `test_06`, `test_07`, `test_08`, `test_09` |
| **Admin Direct Message Bypass**| `test_10_admin_direct_message_bypass`, `test_11_normal_user_cannot_admin_bypass` |
| **Message Payload Validation** | `test_12_oversized_message_blocked`, `test_13_empty_message_blocked` |
| **XSS Safety** | `test_14_xss_html_payload_handled_safely` |
| **JWT Token Validation** | `test_15_jwt_token_validation_and_tampering` |
| **Text-Only File Sharing** | `test_16_file_upload_disabled` |
| **CSV Formula Injection** | `test_17`, `test_22_csv_whitespace_formula_sanitization` |
| **Malformed Socket Payload** | `test_18_malformed_socket_payload_resilience` |
| **Admin Role Authorization** | `test_19_non_admin_privileged_action_rejection` |
| **Group Messaging** | `test_20`, `test_26_malformed_group_payload_resilience` |
| **Database Failure Resilience** | `test_21_database_failure_handling` |
| **Message Rate Limiting** | `test_23_message_rate_limiting` |
| **Database Reset Safety Guard** | `test_24_reset_db_safety_guard_rejection` |
| **Audit Log Failure Resilience**| `test_25_audit_log_failure_resilience` |

### Full Automated Regression Command
Run in PowerShell:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## 11. Common Maintenance Tasks

### A. How to Change Server Port
1. Open [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py).
2. Edit `PORT = 8080` (or set environment variable `$env:PORT="8080"`).
3. Restart server: `python server.py`.

### B. How to Change Max Message Length
1. Open [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py).
2. Edit `MESSAGE_MAX_LENGTH = 2000`.
3. Run tests: `python -m unittest tests/test_seechat.py`.

### C. How to Change Message Rate Limit
1. Open [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py).
2. Edit `MAX_MESSAGES_PER_SECOND = 10`.

### D. How to Add or Modify Default Users
1. Open [`users.json`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/users.json).
2. Add or edit user entries (e.g. `{"username": "New_Desk", "role": "user", "is_disabled": false}`).
3. Restart server.

### E. How to Run Server Manually
1. Open PowerShell in project directory: `cd "C:\Users\rajeshn\Desktop\Rajesh\Desk Ping"`.
2. Execute: `python server.py`.
3. Open browser: `http://127.0.0.1:8080`.

---

## 12. Files You Should Normally NOT Touch

Do not edit these core files unless specifically authorized:
* [`database/db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/db.py): Core database schema initialization & WAL connection manager.
* [`services/chat_request_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/chat_request_service.py): Core relationship permission logic.
* [`client/index.html`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/index.html) & [`client/styles.css`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/client/styles.css): Visually locked client UI shell.

---

## 13. Production Pending Items

The following items remain intentionally **DOCUMENTED / PENDING** for final office deployment phase:
1. **Live Active Directory / LDAP Integration**: Code structure prepared in `services/ad_service.py`; `AD_AUTH_ENABLED = False` during local dev mode.
2. **Production PostgreSQL Database Cluster**: Connection manager in `database/db.py` prepared; live PostgreSQL connection `NOT TESTED`.
3. **Production Nginx HTTPS Reverse Proxy**: Configuration documented in `server_setup_guide.md`; live Nginx deployment `DOCUMENTED / NOT LIVE DEPLOYED`.
