# 🚀 SeeChat – Remaining Work & Production Deployment Blueprint

**Target Audience**: Studio IT Administrators & Lead Developers  
**Application**: SeeChat Studio Communication Suite  
**Project Location**: `C:\Users\rajeshn\Desktop\Rajesh\Desk Ping`  
**Current Port**: `8080` (Internal Port Preserved)  
**Current Auth Status**: Development Mode (`AD_AUTH_ENABLED = False`)  
**Current Database**: SQLite WAL Mode (`data/seechat_audit.db`)  

This document serves as the master blueprint detailing all remaining tasks required for final enterprise studio deployment, outlining exact files, settings, risk levels, and step-by-step technical instructions.

---

## 1. Active Directory / LDAP Connection

### Task Details
* **1. Task Name**: Active Directory / Enterprise LDAP Connection Activation
* **2. Why It Is Needed**: Enables studio domain authentication so artists and staff log into SeeChat using their official studio workstation credentials rather than local development accounts.
* **3. File(s) to Open**:
  - [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py)
  - [`services/ad_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/ad_service.py)
  - [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py)
* **4. Exact Setting / Function / Section Name**:
  - `AD_AUTH_ENABLED` (Setting in `config.py`)
  - `AD_LDAP_SERVER` (Setting in `config.py`)
  - `AD_DOMAIN` (Setting in `config.py`)
  - `verify_ad_credentials(username, password)` (Function in `services/ad_service.py`)
* **5. Current Value / Current Status**:
  - `AD_AUTH_ENABLED = False`
  - `AD_LDAP_SERVER = "ldaps://192.168.1.100"`
  - `AD_DOMAIN = "STUDIO"`
  - Status: **`DOCUMENTED / NOT LIVE TESTED`**
* **6. What Needs to Change**:
  - Set `AD_AUTH_ENABLED = True` (via environment variable or `config.py`).
  - Update `AD_LDAP_SERVER` with the live Domain Controller IP or FQDN.
  - Update `AD_DOMAIN` with the studio Active Directory domain name.
* **7. Example of the Change**:
  ```python
  # In config.py or via System Environment Variables:
  AD_AUTH_ENABLED = True
  AD_LDAP_SERVER = "ldaps://192.168.10.50"
  AD_DOMAIN = "ANIMATIONSTUDIO"
  ```
* **8. Risk Level**: **CAUTION**
* **9. What to Test After Changing**:
  - Valid studio domain user login (e.g. `john_artist` + AD password) $\rightarrow$ Login succeeds.
  - Invalid password $\rightarrow$ Rejection message: `"Invalid Active Directory domain credentials."`
  - Unknown username / disabled domain user $\rightarrow$ Rejection message: `"Invalid Active Directory domain credentials."` or `"Account is disabled by IT Admin!"`
* **10. When to Do It**: During initial studio staging deployment after domain controller details are confirmed by Studio IT.

> [!IMPORTANT]
> **Zero Password Storage Security Protocol**: SeeChat verifies AD credentials via transient LDAP bind and **NEVER STORES OR LOGS** passwords in DB, CSV, browser storage, stdout, or log files. Passwords are discarded immediately after the bind attempt.

---

## 2. PostgreSQL Production Database Switch

### Task Details
* **1. Task Name**: PostgreSQL Production Database Connection Switch
* **2. Why It Is Needed**: Upgrades persistence from single-file SQLite to a multi-threaded PostgreSQL database cluster for enterprise concurrency, central backups, and production durability.
* **3. File(s) to Open**:
  - [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py)
  - [`database/db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/db.py)
  - [`requirements.txt`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/requirements.txt)
* **4. Exact Setting / Function / Section Name**:
  - `DATABASE_URL` (Setting in `config.py`)
  - `DATABASE_TYPE` (Setting in `config.py`)
  - `get_connection()` (Function in `database/db.py`)
  - `init_db()` (Function in `database/db.py`)
* **5. Current Value / Current Status**:
  - `DATABASE_URL = ""`
  - `DATABASE_TYPE = "sqlite"`
  - Active Dev DB: `data/seechat_audit.db` (SQLite WAL)
  - Status: **`PREPARED / NOT LIVE TESTED`** (`psycopg2-binary` installed)
* **6. What Needs to Change**:
  - Set the system environment variable `DATABASE_URL` with the studio PostgreSQL connection string.
* **7. Example of the Change**:
  ```powershell
  # Set environment variable before launching server:
  $env:DATABASE_URL="postgresql://seechat_admin:StudioPass2026@192.168.10.60:5432/seechat_prod_db"
  python server.py
  ```
* **8. Risk Level**: **EXPERT / SECURITY SENSITIVE**
* **9. What to Test After Changing**:
  - Run `python server.py` and verify `init_db()` automatically creates tables (`users`, `messages`, `chat_requests`, `broadcast_groups`) in PostgreSQL.
  - Run test suite: `python -m unittest discover -s tests -p "test_*.py"`.
  - Verify user creation, direct messaging, and group creation execute cleanly without SQL syntax errors.
* **10. When to Do It**: After PostgreSQL server container/instance is provisioned by Database Administrator.

---

## 3. Reverse Proxy & HTTPS (`https://seechat`)

### Task Details
* **1. Task Name**: Nginx / Reverse Proxy Setup for HTTPS (`https://seechat`)
* **2. Why It Is Needed**: Allows studio workstations to access SeeChat at a friendly URL (`https://seechat`) without typing port `:8080`, providing TLS encryption and browser notification permissions.
* **3. File(s) to Open**:
  - [`server_setup_guide.md`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/server_setup_guide.md)
  - [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py)
  - [`server.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/server.py)
* **4. Exact Setting / Function / Section Name**:
  - Nginx Configuration File (`/etc/nginx/conf.d/seechat.conf` or IIS URL Rewrite)
  - `PORT = 8080` (Preserved in `config.py`)
* **5. Current Value / Current Status**:
  - Internal App Port: `8080`
  - Internal Bind: `http://127.0.0.1:8080`
  - Status: **`DOCUMENTED / NOT LIVE DEPLOYED`**
* **6. What Needs to Change**:
  - Install Nginx, IIS, or Caddy on the host gateway server.
  - Configure reverse proxy pass from HTTPS port 443 to `http://127.0.0.1:8080` with WebSocket upgrade headers.
  - Set studio DNS A-record mapping `seechat` $\rightarrow$ Proxy Server IP.
* **7. Example of the Change**:
  ```nginx
  # Nginx reverse proxy configuration snippet
  server {
      listen 443 ssl;
      server_name seechat;
      ssl_certificate /etc/nginx/certs/seechat.crt;
      ssl_certificate_key /etc/nginx/certs/seechat.key;

      location / {
          proxy_pass http://127.0.0.1:8080;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "Upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```
* **8. Risk Level**: **CAUTION**
* **9. What to Test After Changing**:
  - Open `https://seechat` in Chrome $\rightarrow$ Renders green HTTPS lock icon.
  - WebSocket connection upgrades cleanly without disconnection loops.
  - Floating desktop popups and browser notifications prompt for permission cleanly.
* **10. When to Do It**: During final network infrastructure deployment.

---

## 4. Production Secret Key Configuration

### Task Details
* **1. Task Name**: Production Cryptographic Secret Key Configuration
* **2. Why It Is Needed**: Secures JWT token signatures (`HS256`) against forgery or token tampering in production.
* **3. File(s) to Open**:
  - [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py)
* **4. Exact Setting / Function / Section Name**:
  - `SECRET_KEY` (Setting in `config.py`)
* **5. Current Value / Current Status**:
  - Default Fallback: `'seechat_lan_enterprise_jwt_secret_2026_hs256'`
  - Status: **`DEVELOPMENT FALLBACK ACTIVE`**
* **6. What Needs to Change**:
  - Export a 64-character random high-entropy secret in system environment variable `SEECHAT_SECRET_KEY`.
* **7. Example of the Change**:
  ```powershell
  # Set environment variable on production server:
  $env:SEECHAT_SECRET_KEY="c8f93a10b47e29d51e3a6c4f7b2e9d8a1c0f4e7b2a5d8c3e6f9a0b1c2d3e4f5a"
  ```
* **8. Risk Level**: **EXPERT / SECURITY SENSITIVE**
* **9. What to Test After Changing**:
  - Run `python server.py` $\rightarrow$ Startup banner confirms secret loaded.
  - Run `test_15_jwt_token_validation_and_tampering` $\rightarrow$ Tampered tokens rejected.
* **10. When to Do It**: Immediately prior to production server launch.

---

## 5. Development Accounts & Passwordless Login Transition

### Task Details
* **1. Task Name**: Development Accounts & Seed User Transition
* **2. Why It Is Needed**: Explains how local development accounts (`users.json`) behave when switching to live Active Directory authentication.
* **3. File(s) to Open**:
  - [`users.json`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/users.json)
  - [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py)
  - [`database/users.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/users.py)
* **4. Exact Setting / Function / Section Name**:
  - `seed_default_users()` (Function in `database/users.py`)
  - `authenticate_user()` (Function in `services/auth_service.py`)
* **5. Current Value / Current Status**:
  - Development mode allows local workstation logins seeded from `users.json`.
  - Status: **`DEVELOPMENT PRESERVED`**
* **6. What Needs to Change**:
  - When `AD_AUTH_ENABLED = True`, `services/auth_service.py` delegates password verification to Active Directory LDAP bind. `users.json` serves solely to set default initial admin roles (`role: "admin"`).
* **7. Example of the Change**: No code edit required. Changing `AD_AUTH_ENABLED = True` automatically transitions authentication behavior.
* **8. Risk Level**: **CAUTION**
* **9. What to Test After Changing**:
  - Test authenticating as `Admin` and `Demo_User` with AD credentials.
* **10. When to Do It**: Handled automatically when Active Directory is enabled.

---

## 6. Benchmark & Test Users Cleanup

### Task Details
* **1. Task Name**: Benchmark & Scale Test Data Cleanup
* **2. Why It Is Needed**: Removes temporary load test user accounts (`BenchUser_*`, `LoadUser_*`) and test messages created during scalability testing to leave a clean production database.
* **3. File(s) / Data to Open**:
  - `data/seechat_audit.db` (SQLite) / PostgreSQL DB
  - `database/users.py`
  - `database/messages.py`
  - `database/chat_requests.py`
  - `database/groups.py`
  - `chat_logs/` directory
* **4. Exact Setting / Function / Section Name**:
  - Database SQL DELETE Queries
* **5. Current Value / Current Status**:
  - ~1061 test users and associated test chat requests exist in development DB.
  - Status: **`PRESERVED FOR FINAL TESTING`**
* **6. What Needs to Change**:
  - Execute a targeted SQL cleanup query to delete records matching `BenchUser_%` and `LoadUser_%`.
* **7. Example of Cleanup Query**:
  ```sql
  -- Run ONLY at final handover:
  DELETE FROM messages WHERE sender LIKE 'BenchUser_%' OR recipient LIKE 'BenchUser_%' OR sender LIKE 'LoadUser_%' OR recipient LIKE 'LoadUser_%';
  DELETE FROM chat_requests WHERE requester LIKE 'BenchUser_%' OR recipient LIKE 'BenchUser_%' OR requester LIKE 'LoadUser_%' OR recipient LIKE 'LoadUser_%';
  DELETE FROM users WHERE username LIKE 'BenchUser_%' OR username LIKE 'LoadUser_%';
  ```
* **8. Risk Level**: **CAUTION**
* **9. What to Test After Changing**:
  - Query `SELECT COUNT(*) FROM users;` $\rightarrow$ Returns real workstation count (~6-10 default users).
  - Main UI users list displays clean workstation list without test accounts.
* **10. When to Do It**: **ONCE ONLY** at the final deployment stage after all technical verification is finished.

---

## 7. Final Office Pilot Checklist

Complete this checklist during the live studio pilot run:

- [ ] **Manual Server Startup**: Execute `python server.py` on gateway server $\rightarrow$ Banner shows Port `8080`, Gevent Engine, Ready.
- [ ] **HTTP Access**: Open `http://127.0.0.1:8080` in Chrome $\rightarrow$ Messenger shell renders cleanly.
- [ ] **Active Directory Login**: Test domain user login $\rightarrow$ Authenticates against LDAP DC.
- [ ] **Chat Request Creation**: Send request from Artist Desk A to Artist Desk B $\rightarrow$ Card appears with Accept / Decline buttons.
- [ ] **Chat Request Accept**: Click 'Accept' $\rightarrow$ Real-time Socket status updates to `ACCEPTED`; message bar unlocks.
- [ ] **Direct Messaging**: Exchange text messages between workstations $\rightarrow$ Messages appear instantly with timestamps.
- [ ] **Broadcast Group Creation**: Create group `VFX_Comp_Team` $\rightarrow$ Add workstations $\rightarrow$ Group appears in tab.
- [ ] **Group Broadcast**: Send message to group $\rightarrow$ Broadcasts to all group members.
- [ ] **Desktop Popups**: Unfocus browser tab $\rightarrow$ Incoming message opens `popup.html` floating window.
- [ ] **Tab Title Blinking**: Unfocus tab $\rightarrow$ Tab blinks `⚡ (NEW MSG) User Name`.
- [ ] **Connection Reconnect**: Disconnect network for 5s and reconnect $\rightarrow$ Socket restores session without data loss.
- [ ] **Admin User Disable**: Log into Admin console $\rightarrow$ Toggle user disabled $\rightarrow$ User instantly blocked from sending msgs.
- [ ] **Logout**: Click 'Logout' $\rightarrow$ Clears `localStorage` session and returns to login modal overlay.
- [ ] **Server Restart**: Restart `python server.py` $\rightarrow$ Connected clients auto-reconnect cleanly.

---

## 8. Final Backup & Restore Plan

### Backup Procedure Before Deployment
1. **Database**: Copy `data/seechat_audit.db` using safe SQLite online backup API:
   ```python
   import sqlite3
   src = sqlite3.connect('data/seechat_audit.db')
   dst = sqlite3.connect('backups/seechat_audit_pre_deploy.db')
   with dst: src.backup(dst)
   dst.close(); src.close()
   ```
2. **Audit CSV Logs**: Copy `chat_logs/` folder (`xcopy /E /I chat_logs backups\chat_logs_archive`).
3. **Configuration & Users**: Backup `config.py` and `users.json`.

### Restore Verification
1. Stop server process (`auto_run_server.py` or `server.py`).
2. Restore backup copy of `seechat_audit.db` to `data/`.
3. Restart server and verify chat history loads cleanly in browser.

---

## 9. Final Production User Guide PDF (Pending Outline)

A simple, user-facing PDF quick-start guide should be provided to studio artists covering:

1. **How to Open SeeChat**: Open Chrome and navigate to `https://seechat`.
2. **Logging In**: Enter your studio workstation username and domain password.
3. **Sending a Chat Request**: Click a team member in the Directory list and click "Request Chat Permission".
4. **Accepting a Chat Request**: When a prompt card appears, click "Accept" to start messaging.
5. **Direct Messaging**: Type your message (up to 2000 characters) and press Enter or click Send.
6. **Group Messaging**: Switch to the "Groups" tab to communicate with your department group.
7. **Floating Notifications**: Allow browser notification prompts to receive floating desktop alerts when Chrome is minimized.
8. **Logging Out**: Click the Logout icon at the bottom of the sidebar when leaving your workstation.

---

## 10. Final Code Freeze & Version Snapshot

* **Current Code Freeze Status**: **`CODE FREEZE APPROVED WITH WARNINGS`**
* **Git Version Tagging**: When all production tasks are finished, tag the repository:
  ```powershell
  git tag -a v1.0.0-production -m "SeeChat Studio Messenger v1.0.0 Production Release"
  ```
* **Files Included in Release**: All source modules (`server.py`, `config.py`, `database/`, `services/`, `socket_handlers/`, `client/`, `tests/`).
* **Files NEVER Committed to Version Control**:
  - TLS Private Keys (`key.pem`, `cert.pem`, `*.pem`)
  - Environment Files (`.env`, `SEECHAT_SECRET_KEY`)
  - Active Databases (`data/*.db`)
  - Temporary Benchmark CSV Logs (`chat_logs/LoadUser_*/`, `chat_logs/BenchUser_*/`)

---

## 📋 11. Final Implementation Roadmap & Master Summary Table

### Implementation Sequence

```text
CURRENT STATUS (Code Frozen, 26/26 Tests Passed, Dev Mode Active)
       ↓
1. Active Directory LDAP Connection Configured
       ↓
2. PostgreSQL Database Connection Set (Optional Enterprise DB)
       ↓
3. Nginx HTTPS Reverse Proxy & DNS (https://seechat) Set Up
       ↓
4. Office Pilot Checklist Executed
       ↓
5. Benchmark User SQL Cleanup Executed
       ↓
6. User Guide PDF Distributed to Artists
       ↓
7. Final Backup & Git Version Tag Snapshot Created
       ↓
PRODUCTION LIVE
```

### Master Pending Tasks Quick Reference Table

| Pending Task | Main File(s) | Risk Level | Current Status |
| :--- | :--- | :--- | :--- |
| **1. AD / LDAP Integration** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) / [`services/ad_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/ad_service.py) | **CAUTION** | `AD_AUTH_ENABLED = False` (Dev Mode) |
| **2. PostgreSQL Database** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) / [`database/db.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/database/db.py) | **EXPERT / SECURITY** | SQLite WAL Active (`PREPARED`) |
| **3. HTTPS Reverse Proxy** | [`server_setup_guide.md`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/server_setup_guide.md) | **CAUTION** | Port `8080` (`DOCUMENTED`) |
| **4. Secret Key Config** | [`config.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/config.py) | **EXPERT / SECURITY** | Development Fallback Active |
| **5. Dev Account Transition**| [`services/auth_service.py`](file:///C:/Users/rajeshn/Desktop/Rajesh/Desk%20Ping/services/auth_service.py) | **CAUTION** | Passwordless Dev Login Active |
| **6. Benchmark Data Cleanup**| `data/seechat_audit.db` | **CAUTION** | ~1061 Test Users Preserved |
| **7. Office Pilot Checklist** | Pilot Execution | **SAFE** | Staging Checklist Ready |
| **8. Final Backup & Restore** | `database/db.py` | **SAFE** | Procedure Documented |
| **9. End-User Guide PDF** | Documentation | **SAFE** | Outline Documented |
| **10. Version Snapshot Tag** | Git Release Tag | **SAFE** | Ready for Tagging (`v1.0.0`) |
