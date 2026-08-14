import time
import jwt
import config
from database.db import get_connection
from database.users import get_user_by_username, update_user_status
from services.ad_service import verify_ad_credentials

def generate_jwt_token(username, role):
    payload = {
        'username': username,
        'role': role,
        'iat': int(time.time()),
        'exp': int(time.time()) + config.JWT_EXPIRATION_SECONDS
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

def verify_jwt_token(token):
    if not token:
        return None
    try:
        decoded = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return decoded
    except Exception:
        return None

def authenticate_user(username, password, client_ip):
    """
    Unified Authentication Service:
    Checks config.AD_AUTH_ENABLED. If True -> verifies with Active Directory.
    If False -> uses Local/Development Authentication.
    """
    if not username or not username.strip():
        return False, 'user', "Username is required.", None
        
    username = username.strip()
    user_info = get_user_by_username(username)
    
    if not user_info:
        role = 'admin' if 'admin' in username.lower() else 'user'
        conn, db_engine = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, ip_address, status, is_disabled)
            VALUES (?, '', ?, ?, 'online', 0)
        """, (username, role, client_ip))
        conn.commit()
        conn.close()
        user_info = get_user_by_username(username)

    if user_info and user_info.get('is_disabled'):
        return False, 'user', "Account is disabled by IT Admin! Contact Systems Team.", None

    if config.AD_AUTH_ENABLED:
        # Active Directory Authentication Mode
        ad_success, ad_msg = verify_ad_credentials(username, password)
        if not ad_success:
            return False, 'user', ad_msg, None
        
        role = user_info['role'] if user_info else ('admin' if 'admin' in username.lower() else 'user')
    else:
        # Development / Local Testing Authentication Mode
        role = user_info['role'] if user_info else ('admin' if 'admin' in username.lower() else 'user')

    # Update user status & IP in DB
    update_user_status(username, client_ip, status='online')
    
    # Issue cryptographic JWT token (No password inside token)
    token = generate_jwt_token(username, role)
    return True, role, "Authenticated", token
