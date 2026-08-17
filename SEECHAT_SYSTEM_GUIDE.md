# SeeChat – Internal Communication Platform
### System Overview, Security & Review Guide

**Current Phase:** Internal Review  
**Deployment:** Internal Office Network  
**Proposed Internal URL:** `https://seechat/`  

---

## 1. System Overview

SeeChat is an internal communication application designed for employees working on the company network.

It provides real-time text communication, group communication, user availability information and administrative controls within the internal environment.

| Attribute | Details |
| --- | --- |
| **System** | SeeChat |
| **Purpose** | Internal Team Communication |
| **Network** | Internal Office Network |
| **Internet Requirement** | Public internet is not required for core communication |
| **Current Authentication** | Local test authentication |
| **Planned Authentication** | Active Directory after approval |
| **Current Status** | Ready for Internal Review |

---

## 2. Why SeeChat

In daily office operations, communication challenges can arise:
- Employees may work inside full-screen applications and may miss browser or email communication.
- Teams may sometimes need quick internal communication.
- An internally managed communication option provides better control over access and availability.
- The IT team can manage user access centrally.
- The application is intended strictly for communication within the company network.

---

## 3. System Components

SeeChat is structured into three main parts:

### Frontend
The frontend is the interface employees use in the browser.

Examples include:
- Team Directory
- Chat Interface
- Broadcast Groups
- System Notifications
- User Search
- Admin Console

### Backend
The backend runs on the SeeChat server and manages application logic and communication.

Functions include:
- Validates user sessions
- Checks communication permissions
- Routes communication to intended recipients
- Manages broadcast groups
- Manages user status updates
- Applies security rules

### Database
The local application database maintains the application information required for user access, communication features, groups and status management.

---

## 4. System Flow

```text
Employee Workstation
        │
        ▼
Proposed Internal URL
https://seechat/
        │
        ▼
Internal Network / DNS
        │
        ▼
Secure HTTPS Connection
        │
        ▼
SeeChat Server
        │
        ├── User Access
        ├── Communication
        ├── Groups
        ├── Notifications
        └── Administration
        │
        ▼
Local Application Database


After Approval:

SeeChat Server ───> Company Active Directory
```

---

## 5. How SeeChat Works

1. **01 Access Application:** User opens SeeChat at `https://seechat/`.
2. **02 Verify Access:** User access is verified by the server.
3. **03 Display Directory:** Team Directory is displayed with user availability.
4. **04 Select Target:** User selects a team member or group.
5. **05 Check Permission:** Communication permission is checked.
6. **06 Send Message:** User sends a message.
7. **07 Validate Request:** SeeChat validates the request.
8. **08 Route Communication:** Communication is routed to the intended user.
9. **09 Update Status:** Sent, Delivered and Read status is updated.
10. **10 Update Unread State:** Unread indicators are updated automatically.

---

## 6. Main Features

### Communication
- **Direct Messaging:** Instant text communication between team members.
- **Chat Requests:** Permission workflow requiring approval before initiating chats with new users.
- **Groups:** Multi-user groups for team notifications and announcements.
- **Reply:** Quoted message previews for contextual clarity.
- **Quick Replies:** Common predefined replies for faster communication.

### Message Controls
- **Sent / Delivered / Read:** Visual status indicators for message delivery.
- **Unread Indicators:** Numeric indicators for unread incoming messages.
- **Typing Indicator:** Real-time indication when a partner is typing.
- **Emoji & Reactions:** Quick message acknowledgments without adding chat clutter.
- **Edit Own Message:** Ability for senders to edit their own messages.
- **Delete Own Message:** Ability for senders to delete their own messages.
- **Clear Chat:** Per-user option to clear local chat history.

### Workplace Features
- **Presence / Availability:** Automatic status indicating Available or Away workstation states.
- **Call to Desk:** Urgent internal notification pings requesting in-person collaboration.
- **Birthday Cards:** Card-based birthday wishes and predefined thank-you responses.
- **Search:** Instant team member search.
- **Conversation Pinning:** Ability to pin important conversations to the top of the list.

### Administration
- **User Management:** Create user accounts.
- **Enable / Disable Accounts:** Enable or disable user access.
- **Role Management:** Manage User and Admin privileges.
- **Group Management:** Create, edit members, rename, or delete groups.
- **System Announcements:** Broadcast system-wide pop-up notices to all connected workstations.
- **System Health:** Monitor active connections and database status.

---

## 7. Security Controls

### Network
- Designed for internal network use.
- Proposed HTTPS access.
- Public internet not required for core communication.

### User Access
- Authenticated user sessions.
- User identity checked by the server.
- Admin actions restricted by role.

### Application Protection
- Input validation against malicious input.
- Protection against common web input attacks.
- Database queries use safe parameter handling.
- Server-side rate limiting against excessive messaging.

### System Protection
- Does not disable antivirus or local security software.
- Does not modify firewall automatically.
- Does not create hidden startup persistence.
- TLS private keys are kept separate from the frontend.

---

## 8. Current Verification Status

| Verification Metric | Result | Status |
| --- | --- | --- |
| **Automated Tests** | **37 / 37** | PASS |
| **Chrome** | Verified | PASS |
| **Edge** | Verified | PASS |
| **Server Startup** | Verified | PASS |
| **Browser Console Errors** | 0 | PASS |
| **Server Errors** | 0 | PASS |
| **Private Communication Routing** | Verified | PASS |
| **Offline Core Operation** | Verified | PASS |
| **Code & Security Review** | Completed | PASS |

---

## 9. Proposed HTTPS Setup

The proposed internal address is:

```text
https://seechat/
```

The final hostname and HTTPS configuration will be confirmed with the IT team before deployment.

Technical support from the IT team may be required for:
- Internal hostname / DNS setup
- Trusted TLS certificate provisioning
- Workstation certificate trust
- Network or reverse proxy configuration if required
- Final hostname confirmation

*No public internet domain needs to be purchased if the required internal DNS and certificate infrastructure is available.*

---

## 10. Planned Active Directory Integration

Active Directory integration is currently disabled and will be configured only after the required internal review and approval.

### Planned Access Flow:

```text
User opens SeeChat
        │
        ▼
User enters company credentials
        │
        ▼
SeeChat validates the account with Active Directory
        │
        ▼
Authorized user receives access
```

### Benefits:
- Users can use their existing company credentials for SeeChat access.
- Access can follow company account status.
- User account management can remain centralized with the IT team.

---

## 11. Review & Deployment Process

```text
COMPLETED

Development
    │
    ▼
Internal Functional Testing
    │
    ▼
Code & Security Review


CURRENT

Internal Management / IT / Security Review


NEXT

Endpoint / Antivirus Scan
    │
    ▼
HTTPS / DNS Configuration
    │
    ▼
Active Directory Integration
    │
    ▼
Controlled Office Testing
    │
    ▼
Production Deployment
```

---

## 12. System Boundaries

SeeChat is **not** designed to:
- Depend on public social media accounts.
- Depend on external cloud messaging for core communication.
- Provide unrestricted file sharing.
- Modify firewall settings automatically.
- Disable antivirus or security software.
- Create hidden system persistence.

---

## 13. Current Status

SeeChat has completed the current development and internal verification stage and is ready for management, IT and security review.

Pending Review Items:
1. Final functional review
2. Endpoint / antivirus scan
3. IT and security review
4. HTTPS / DNS configuration confirmation
5. Management review / approval

**Proposed Internal URL:** `https://seechat/`  