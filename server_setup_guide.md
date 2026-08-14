# 🛡️ SeeChat - Studio Production Server Setup & Security Guide

This document provides step-by-step instructions for deploying **SeeChat** on a dedicated studio server with **HTTPS Reverse Proxy (`https://seechat`)**, **PostgreSQL database connection**, and **Active Directory (AD LDAP) authentication**.

---

## 🌐 1. Production Architecture Overview

```text
Browser User
     ↓
https://seechat  (HTTPS Port 443)
     ↓
Reverse Proxy (Nginx / IIS / Caddy)
     ↓
localhost:8080  (Internal Port 8080 Preserved)
     ↓
SeeChat Python Server
```

---

## 📋 2. Dependencies & Installation

### Requirements:
- **Operating System**: Windows Server / Windows 10/11 / Rocky Linux / Ubuntu Server
- **Python Version**: Python 3.9+ or 3.10+
- **Database Engine**: PostgreSQL 12+ (or SQLite WAL for dev testing)

### Installation Commands:
```powershell
# 1. Navigate to project root
cd "C:\Users\rajeshn\Desktop\Rajesh\Desk Ping"

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Start SeeChat Server
python server.py
```

---

## 🔒 3. Active Directory (AD / LDAP) Integration

To enable Active Directory login for final production deployment, update `config.py` or set environment variables:

```python
AD_AUTH_ENABLED = True
AD_LDAP_SERVER = "ldaps://192.168.1.100"  # Studio Domain Controller IP
AD_DOMAIN = "STUDIO"                    # Enterprise Domain Name
```

> [!IMPORTANT]
> **Zero AD Password Storage**: SeeChat verifies AD credentials via transient LDAP bind and **NEVER STORES OR LOGS** passwords in DB, CSV, browser storage, or log files.

---

## 🌐 4. Nginx Reverse Proxy Setup (`https://seechat`)

To allow studio artists to access SeeChat at `https://seechat` without typing port `:8080`, create `/etc/nginx/conf.d/seechat.conf`:

```nginx
server {
    listen 80;
    server_name seechat;
    return 301 https://$host$request_uri;
}

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 💾 5. PostgreSQL Database Configuration

Set the environment variable `DATABASE_URL` before launching `server.py`:
```cmd
set DATABASE_URL=postgresql://seechat_user:secretpass@127.0.0.1:5432/seechat_db
python server.py
```
