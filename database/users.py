import json
import os
from database.db import get_connection
import config

def sync_users_json_from_db():
    try:
        conn, db_engine = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, is_disabled FROM users ORDER BY username ASC")
        rows = cursor.fetchall()
        conn.close()
        
        users_list = []
        for r in rows:
            users_list.append({
                'username': r['username'],
                'role': r['role'] or 'user',
                'is_disabled': bool(r['is_disabled'])
            })
            
        with open(config.USERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(users_list, f, indent=2)
    except Exception:
        pass

def seed_default_users():
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    default_users = []
    if os.path.exists(config.USERS_JSON_PATH):
        try:
            with open(config.USERS_JSON_PATH, 'r', encoding='utf-8') as f:
                default_users = json.load(f)
        except Exception:
            pass

    if not default_users:
        default_users = [
            {"username": "Demo_User", "role": "user", "is_disabled": False},
            {"username": "Admin", "role": "admin", "is_disabled": False},
            {"username": "Support_Desk", "role": "user", "is_disabled": False},
            {"username": "Sales_Desk", "role": "user", "is_disabled": False},
            {"username": "HR_Desk", "role": "user", "is_disabled": False},
            {"username": "IT_Desk", "role": "admin", "is_disabled": False}
        ]
    
    for u in default_users:
        uname = u.get('username')
        if not uname:
            continue
        role = u.get('role', 'admin' if 'admin' in uname.lower() else 'user')
        is_disabled = 1 if u.get('is_disabled', False) else 0
        
        cursor.execute("SELECT username FROM users WHERE username = ?", (uname,))
        row = cursor.fetchone()
        
        if row is None:
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, ip_address, status, is_disabled, mood_status)
                VALUES (?, '', ?, '127.0.0.1', 'offline', ?, 'Available')
            """, (uname, role, is_disabled))
        else:
            cursor.execute("""
                UPDATE users SET role = ?, is_disabled = ? WHERE username = ?
            """, (role, is_disabled, uname))
            
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, role, ip_address, status, is_disabled, mood_status FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_registered_users():
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, status, ip_address, is_disabled, last_seen, mood_status FROM users ORDER BY username ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_user_status(username, ip_address, status='online'):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET ip_address = ?, status = ?, last_seen = CURRENT_TIMESTAMP
        WHERE username = ?
    """, (ip_address, status, username))
    conn.commit()
    conn.close()

def update_user_mood_status(username, mood_status):
    VALID_MOODS = ['Available', 'Busy', 'In Meeting', 'On Break', 'Rendering 😄']
    if mood_status not in VALID_MOODS:
        mood_status = 'Available'
        
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mood_status = ? WHERE username = ?", (mood_status, username))
    conn.commit()
    conn.close()
    return True, mood_status

def toggle_user_disabled(username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_disabled FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
    
    new_val = 0 if row['is_disabled'] else 1
    cursor.execute("UPDATE users SET is_disabled = ? WHERE username = ?", (new_val, username))
    conn.commit()
    conn.close()
    sync_users_json_from_db()
    
    msg = "Account disabled successfully." if new_val == 1 else "Account enabled successfully."
    return True, msg

def toggle_user_role(username, target_role=None):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
    
    if target_role and target_role in ['user', 'admin']:
        new_role = target_role
    else:
        new_role = 'user' if row['role'] == 'admin' else 'admin'
        
    cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
    conn.commit()
    conn.close()
    sync_users_json_from_db()
    return True, f"Role updated to {new_role.upper()} successfully."

def delete_user_by_admin(username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        conn.close()
        return False, "User not found."
        
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    sync_users_json_from_db()
    return True, "User deleted successfully."

def add_user_by_admin(username, role='user'):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists."
        
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, ip_address, status, is_disabled, mood_status)
        VALUES (?, '', ?, '127.0.0.1', 'offline', 0, 'Available')
    """, (username, role))
    conn.commit()
    conn.close()
    sync_users_json_from_db()
    return True, "User created successfully."
