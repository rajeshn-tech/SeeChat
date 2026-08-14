from datetime import datetime
from database.db import get_connection

def save_message(message_id, sender, recipient, broadcast_group, message, ip_address, reply_to_id=''):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    ts_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    cursor.execute("""
        INSERT INTO messages (message_id, sender, recipient, broadcast_group, message, ip_address, timestamp, status, reply_to_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'sent', ?)
    """, (message_id, sender, recipient, broadcast_group or '', message, ip_address, ts_now, reply_to_id or ''))
    conn.commit()
    conn.close()
    return ts_now

def get_message_reactions(message_id):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emoji, COUNT(*) as cnt, GROUP_CONCAT(username) as users
        FROM message_reactions
        WHERE message_id = ?
        GROUP BY emoji
    """, (message_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        user_list = r['users'].split(',') if r['users'] else []
        result.append({
            'emoji': r['emoji'],
            'count': r['cnt'],
            'users': user_list
        })
    return result

def toggle_reaction(message_id, username, emoji):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    # Check if target message is deleted
    cursor.execute("SELECT is_deleted FROM messages WHERE message_id = ?", (message_id,))
    msg_row = cursor.fetchone()
    if msg_row and msg_row['is_deleted']:
        conn.close()
        return get_message_reactions(message_id)

    cursor.execute("SELECT emoji FROM message_reactions WHERE message_id = ? AND username = ?", (message_id, username))
    row = cursor.fetchone()
    
    if row:
        if row['emoji'] == emoji:
            cursor.execute("DELETE FROM message_reactions WHERE message_id = ? AND username = ?", (message_id, username))
        else:
            cursor.execute("UPDATE message_reactions SET emoji = ?, created_at = CURRENT_TIMESTAMP WHERE message_id = ? AND username = ?", (emoji, message_id, username))
    else:
        cursor.execute("INSERT INTO message_reactions (message_id, username, emoji) VALUES (?, ?, ?)", (message_id, username, emoji))
        
    conn.commit()
    conn.close()
    return get_message_reactions(message_id)

def get_message_by_id(message_id):
    if not message_id:
        return None
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message_id, sender, recipient, message, is_edited, edited_at, is_deleted, deleted_at FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    if res.get('is_deleted'):
        res['message'] = 'Message deleted'
    return res

def edit_message(message_id, username, new_text):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message, is_deleted FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Message not found.", None
    if row['sender'] != username:
        conn.close()
        return False, "Unauthorized. You can only edit your own messages.", None
    if row['is_deleted']:
        conn.close()
        return False, "Cannot edit a deleted message.", None

    prev_text = row['message']
    ts_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # Calculate revision number
    cursor.execute("SELECT COUNT(*) as cnt FROM message_edits WHERE message_id = ?", (message_id,))
    rev_cnt = cursor.fetchone()['cnt']
    revision_num = rev_cnt + 1

    # Insert audit record
    cursor.execute("""
        INSERT INTO message_edits (message_id, revision_number, previous_text, new_text, edited_by, edited_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (message_id, revision_num, prev_text, new_text, username, ts_now))

    # Update messages table
    cursor.execute("""
        UPDATE messages
        SET message = ?, is_edited = 1, edited_at = ?
        WHERE message_id = ?
    """, (new_text, ts_now, message_id))

    conn.commit()
    conn.close()

    updated_msg = get_message_by_id(message_id)
    return True, "Message updated successfully", updated_msg

def delete_message(message_id, username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message, is_deleted FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Message not found.", None
    if row['sender'] != username:
        conn.close()
        return False, "Unauthorized. You can only delete your own messages.", None
    if row['is_deleted']:
        conn.close()
        return True, "Message already deleted.", get_message_by_id(message_id)

    orig_text = row['message']
    ts_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # Insert audit record
    cursor.execute("""
        INSERT INTO message_deletes (message_id, original_message, deleted_by, deleted_at)
        VALUES (?, ?, ?, ?)
    """, (message_id, orig_text, username, ts_now))

    # Soft delete in messages table
    cursor.execute("""
        UPDATE messages
        SET is_deleted = 1, deleted_at = ?
        WHERE message_id = ?
    """, (ts_now, message_id))

    conn.commit()
    conn.close()

    deleted_msg = get_message_by_id(message_id)
    return True, "Message deleted successfully", deleted_msg

def get_chat_history(user1, user2, limit=100):
    """
    Retrieves chat history between user1 and user2.
    If user1 has previously cleared chat with user2, filters out messages timestamp <= cleared_at for user1.
    Attaches reactions and reply_preview for each message.
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT cleared_at FROM user_chat_clears WHERE username = ? AND target = ?", (user1, user2))
    row = cursor.fetchone()
    cleared_at = row['cleared_at'] if row else None
    
    if cleared_at:
        cursor.execute("""
            SELECT * FROM messages 
            WHERE ((sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?))
              AND timestamp > ?
            ORDER BY timestamp ASC LIMIT ?
        """, (user1, user2, user2, user1, cleared_at, limit))
    else:
        cursor.execute("""
            SELECT * FROM messages 
            WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?)
            ORDER BY timestamp ASC LIMIT ?
        """, (user1, user2, user2, user1, limit))
        
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Enrich rows with reactions & reply details
    msg_map = {m['message_id']: m for m in rows}
    for m in rows:
        if m.get('is_deleted'):
            m['message'] = 'Message deleted'
            m['reactions'] = []
        else:
            m['reactions'] = get_message_reactions(m['message_id'])

        if m.get('reply_to_id'):
            ref_msg = msg_map.get(m['reply_to_id']) or get_message_by_id(m['reply_to_id'])
            if ref_msg:
                m['reply_preview'] = {
                    'message_id': ref_msg['message_id'],
                    'sender': ref_msg['sender'],
                    'message': 'Message deleted' if ref_msg.get('is_deleted') else ref_msg['message']
                }
    return rows

def update_message_status(message_id, status):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE messages 
        SET status = ?, seen_at = CASE WHEN ? = 'read' THEN CURRENT_TIMESTAMP ELSE seen_at END
        WHERE message_id = ?
    """, (status, status, message_id))
    conn.commit()
    conn.close()

def update_message_status_delivered(message_id, recipient):
    """
    Verifies that the authenticated recipient is the intended recipient of message_id.
    Updates status to 'delivered' if currently 'sent'.
    Returns (success, sender, recipient, message_id).
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, recipient, status FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, None, None, message_id
    
    sender, intended_recipient, current_status = row['sender'], row['recipient'], row['status']
    if intended_recipient != recipient:
        conn.close()
        return False, None, None, message_id
        
    if current_status == 'sent':
        cursor.execute("UPDATE messages SET status = 'delivered' WHERE message_id = ?", (message_id,))
        conn.commit()
        
    conn.close()
    return True, sender, intended_recipient, message_id

def mark_messages_as_read(sender, recipient):
    """
    Marks all unread messages from 'sender' to 'recipient' (where recipient is viewing) as 'read'.
    Returns list of updated message dicts/ids and sender name.
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_id FROM messages 
        WHERE sender = ? AND recipient = ? AND status IN ('sent', 'delivered')
    """, (sender, recipient))
    rows = cursor.fetchall()
    updated_ids = [r['message_id'] for r in rows]
    
    if updated_ids:
        cursor.execute("""
            UPDATE messages 
            SET status = 'read', seen_at = CURRENT_TIMESTAMP
            WHERE sender = ? AND recipient = ? AND status IN ('sent', 'delivered')
        """, (sender, recipient))
        conn.commit()
        
    conn.close()
    return updated_ids, sender, recipient

def get_unread_counts(username):
    """
    Returns a dictionary of { sender_username: unread_count } for unread messages sent to 'username'.
    Filters out messages prior to username's cleared_at timestamp for that sender.
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.sender, COUNT(*) as cnt 
        FROM messages m
        LEFT JOIN user_chat_clears c ON c.username = ? AND c.target = m.sender
        WHERE m.recipient = ? 
          AND m.status IN ('sent', 'delivered')
          AND (c.cleared_at IS NULL OR m.timestamp > c.cleared_at)
        GROUP BY m.sender
    """, (username, username))
    rows = cursor.fetchall()
    conn.close()
    counts = {r['sender']: r['cnt'] for r in rows}
    return counts

def clear_chat_with_target(user1, target):
    """
    Per-user chat clear: records user1's cleared_at timestamp for 'target'.
    Does NOT delete physical rows from messages table so partner retains complete history.
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    ts_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    if db_engine == 'sqlite':
        cursor.execute("""
            INSERT INTO user_chat_clears (username, target, cleared_at)
            VALUES (?, ?, ?)
            ON CONFLICT(username, target) DO UPDATE SET cleared_at = excluded.cleared_at
        """, (user1, target, ts_now))
    else:
        cursor.execute("""
            INSERT INTO user_chat_clears (username, target, cleared_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (username, target) DO UPDATE SET cleared_at = EXCLUDED.cleared_at
        """, (user1, target, ts_now))
        
    conn.commit()
    conn.close()
