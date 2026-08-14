from database.db import get_connection
import config

def get_chat_request_status(user1, user2):
    if user1 == user2:
        return 'ACCEPTED'
        
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    # Admin direct messaging auto-bypass if enabled
    if config.ADMIN_DIRECT_MESSAGE:
        cursor.execute("SELECT role FROM users WHERE username IN (?, ?)", (user1, user2))
        roles = [r['role'] for r in cursor.fetchall()]
        if 'admin' in roles:
            conn.close()
            return 'ACCEPTED'

    cursor.execute("""
        SELECT sender, recipient, status FROM chat_requests
        WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
    """, (user1, user2, user2, user1))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 'NONE'
    
    status_val = row['status'].upper()
    if status_val == 'ACCEPTED':
        return 'ACCEPTED'
    elif status_val == 'DECLINED' or status_val == 'REJECTED':
        return 'REJECTED'
    
    if row['sender'] == user1:
        return 'PENDING_OUT'
    else:
        return 'PENDING_IN'

def send_chat_request(sender, recipient):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute("""
        SELECT status FROM chat_requests
        WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
    """, (sender, recipient, recipient, sender))
    row = cursor.fetchone()
    
    if row and row['status'].upper() == 'ACCEPTED':
        conn.close()
        return True, 'ACCEPTED'
        
    cursor.execute("""
        INSERT INTO chat_requests (sender, recipient, status)
        VALUES (?, ?, 'pending')
        ON CONFLICT(sender, recipient) DO UPDATE SET status = 'pending'
    """, (sender, recipient))
    conn.commit()
    conn.close()
    return True, 'PENDING_OUT'

def respond_chat_request(user, partner, action):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    # Verify user is intended recipient of request
    cursor.execute("""
        SELECT id, sender, recipient FROM chat_requests
        WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
    """, (partner, user, user, partner))
    row = cursor.fetchone()
    
    status_val = 'accepted' if action.lower() == 'accept' else 'declined'
    
    if row:
        cursor.execute("""
            UPDATE chat_requests SET status = ?
            WHERE id = ?
        """, (status_val, row['id']))
    else:
        cursor.execute("""
            INSERT INTO chat_requests (sender, recipient, status)
            VALUES (?, ?, ?)
        """, (partner, user, status_val))
        
    conn.commit()
    conn.close()
    return True, status_val.upper()
