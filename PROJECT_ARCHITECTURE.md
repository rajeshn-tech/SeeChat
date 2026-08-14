# 🏗️ SeeChat - Project Architecture & Technical Map

This document outlines the complete architectural design, modular component structure, database model, and security data flow of the **SeeChat Studio Messenger**.

---

## 📐 1. System High-Level Architecture

```mermaid
flowchart TD
    subgraph Client Layer (Browser)
        A[User Browser / Workstation] -->|HTTP / HTTPS| B[Flask Application Gateway]
        A -->|WebSocket / WSS| C[Socket.IO Real-Time Engine]
        A -->|System Toast / Popup| D[Native Floating Desktop Window popup.html]
    end

    subgraph Config & Security Layer
        B --> E[config.py Centralized Settings]
        C --> F[services/auth_service.py JWT Auth]
        F --> G[services/ad_service.py AD LDAP Stub]
    end

    subgraph Service & Authorization Layer
        C --> H[socket_handlers/ Real-Time Dispatchers]
        H --> I[services/chat_request_service.py Relationship Validator]
        H --> J[services/chat_service.py Backend Authorization]
        J --> K[services/audit_service.py Compliance CSV Logger]
    end

    subgraph Database Layer
        J --> L[(PostgreSQL Production Engine)]
        J --> M[(SQLite Dev WAL Engine)]
    end
```

---

## 📂 2. Modular File Map & Responsibilities

```text
C:\Users\rajeshn\Desktop\Rajesh\Desk Ping\
├── config.py                       # Centralized App Settings & AD Toggle
├── server.py                       # Modular App Entry Point & SocketIO Host
├── generate_ssl.py                 # RSA SSL/TLS Certificate Generator
├── auto_run_server.py              # Service Watchdog Script
├── requirements.txt                # Production Dependency Specification
├── server_setup_guide.md           # Production Reverse Proxy & Security Deployment Guide
├── PROJECT_ARCHITECTURE.md         # Architecture Map (This File)
├── HOW_TO_CHANGE_FEATURES.md       # Beginner Maintenance Guide
│
├── database/                       # Database Persistence Layer
│   ├── db.py                       # Unified PostgreSQL / SQLite Connection Manager
│   ├── users.py                    # User Profiles, Roles & Disable Flags
│   ├── messages.py                 # Parameterized Message Storage & History
│   ├── chat_requests.py            # Relationship States (NONE, PENDING, ACCEPTED, REJECTED)
│   └── groups.py                   # Broadcast Group Memberships
│
├── services/                       # Business Logic Layer
│   ├── ad_service.py               # Secure LDAP / LDAPS Active Directory Verification
│   ├── auth_service.py             # JWT Token Signing & Session Auth
│   ├── chat_request_service.py     # Backend Relationship Authorization Checks
│   ├── chat_service.py             # Message Validation & Text-Only Enforcement
│   └── audit_service.py            # Compliance CSV Audit Logging
│
├── socket_handlers/               # Socket.IO Event Handlers
│   ├── connection.py               # Connection & Login Events
│   ├── messages.py                 # Direct & Broadcast Messaging Events
│   ├── chat_requests.py            # Request Approval & Response Events
│   ├── presence.py                 # User Online / Offline Status Updates
│   └── groups.py                   # Group Management & Admin Control Events
│
├── tests/                          # Automated Functional & Benchmark Tests
│   ├── test_seechat.py             # Functional Security Test Suite
│   └── load_test.py                # High-Concurrency Socket Load Test
│
└── client/                         # Visual Contract UI Layer (Unchanged)
    ├── index.html                  # Main Messenger Shell & Admin Panel
    ├── popup.html                  # Native Desktop Mini Floating Window
    ├── app.js                      # Client Application Logic & Socket Listener
    ├── styles.css                  # Modern Dark Slate VFX Studio Aesthetics
    └── presentation.html           # Executive Deck Page
```

---

## 🔒 3. Security Data Flow Rules

1. **Active Directory Passwords**:
   - `services/ad_service.py` performs transient LDAP bind verification.
   - **Zero Password Storage**: Passwords are NEVER written to DB, CSV, browser storage, or logs, and are discarded immediately after bind check.

2. **Backend-Enforced Chat Requests**:
   - `services/chat_service.py` invokes `services/chat_request_service.is_chat_allowed(sender, recipient)`.
   - If status is NOT `ACCEPTED` (or authorized Admin bypass), server rejects message delivery.

3. **Text-Only Messaging**:
   - `config.ALLOW_FILE_SHARING = False`. Server strictly rejects attachment payloads and does not expose upload endpoints.
