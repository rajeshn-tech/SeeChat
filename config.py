import os

# ==================================================================
#           SEECHAT ENTERPRISE CONFIGURATION SETTINGS
# ==================================================================

APP_NAME = "SeeChat"
BRANDING_NAME = "SeeChat Studio Communication Suite"

# SERVER NETWORK & PORT CONFIGURATION (Port 8080 Internal Mandatory)
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
ADMIN_DIRECT_MESSAGE = True  # Admin bypass allowed for IT operational communications
MESSAGE_MAX_LENGTH = 2000
ALLOW_FILE_SHARING = False   # Strictly Text-Only Messaging (Zero Upload Endpoints)

# ACTIVE DIRECTORY (AD / LDAP) CONFIGURATION PHASING
# Set to False during development/testing. Set to True for final AD production deployment.
AD_AUTH_ENABLED = os.environ.get('AD_AUTH_ENABLED', 'false').lower() == 'true'
AD_LDAP_SERVER = os.environ.get('AD_LDAP_SERVER', 'ldaps://192.168.1.100')
AD_DOMAIN = os.environ.get('AD_DOMAIN', 'STUDIO')

# DATABASE ENGINE CONFIGURATION
# Default: SQLite WAL mode. Production: PostgreSQL (e.g. postgresql://user:pass@localhost:5432/seechat)
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
