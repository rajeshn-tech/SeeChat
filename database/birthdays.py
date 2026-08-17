from datetime import datetime
from database.db import get_connection

def get_today_birthdays():
    """
    Returns list of dicts: [{'username': '...', 'birth_date': 'MM-DD'}]
    matching today's date (MM-DD format).
    """
    today_mm_dd = datetime.now().strftime('%m-%d')
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, birth_date 
        FROM birthdays 
        WHERE birth_date LIKE ? OR birth_date LIKE ?
    """, (f"%{today_mm_dd}%", f"%{datetime.now().strftime('%m/%d')}%"))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_birthdays():
    """
    Returns all birthday records ordered by birth_date ASC.
    """
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, birth_date, created_at FROM birthdays ORDER BY birth_date ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def set_user_birthday(username, birth_date):
    """
    Adds or updates birthday for a user. Expects birth_date as MM-DD (e.g. '08-17' or '1995-08-17').
    """
    if not username or not birth_date:
        return False, "Username and Birth Date are required."

    username = username.strip()
    birth_date = birth_date.strip()

    conn, db_engine = get_connection()
    cursor = conn.cursor()
    try:
        if db_engine == 'sqlite':
            cursor.execute("""
                INSERT INTO birthdays (username, birth_date)
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET birth_date = excluded.birth_date
            """, (username, birth_date))
        else:
            cursor.execute("""
                INSERT INTO birthdays (username, birth_date)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET birth_date = EXCLUDED.birth_date
            """, (username, birth_date))
        conn.commit()
        conn.close()
        return True, f"Birthday updated for {username} ({birth_date})."
    except Exception as e:
        conn.close()
        return False, f"Failed to update birthday: {e}"

def delete_user_birthday(username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM birthdays WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True, f"Birthday record removed for {username}."

def add_birthday_wish(birthday_user, sender, wish_text):
    if not birthday_user or not sender or not wish_text:
        return False, "Missing parameters."
    
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO birthday_wishes (birthday_user, sender, wish_text)
        VALUES (?, ?, ?)
    """, (birthday_user, sender, wish_text))
    conn.commit()
    wish_id = cursor.lastrowid
    conn.close()
    return True, wish_id

def get_wishes_for_user(birthday_user):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, birthday_user, sender, wish_text, thank_you_text, thank_you_sent, created_at
        FROM birthday_wishes
        WHERE birthday_user = ?
        ORDER BY id DESC
    """, (birthday_user,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def send_thank_you_for_wish(wish_id, thank_you_text):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE birthday_wishes
        SET thank_you_text = ?, thank_you_sent = 1
        WHERE id = ?
    """, (thank_you_text, wish_id))
    conn.commit()
    
    cursor.execute("SELECT sender, birthday_user FROM birthday_wishes WHERE id = ?", (wish_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return True, row['sender'], row['birthday_user']
    return False, None, None

def thank_all_wishes(birthday_user, thank_you_text):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT sender FROM birthday_wishes WHERE birthday_user = ? AND thank_you_sent = 0", (birthday_user,))
    senders = [r['sender'] for r in cursor.fetchall()]
    
    cursor.execute("""
        UPDATE birthday_wishes
        SET thank_you_text = ?, thank_you_sent = 1
        WHERE birthday_user = ? AND thank_you_sent = 0
    """, (thank_you_text, birthday_user))
    conn.commit()
    conn.close()
    return senders

def seed_default_birthdays():
    """
    Seeds sample birthday for Demo_User on today's date for instant live demo testing.
    """
    today_mm_dd = datetime.now().strftime('%m-%d')
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM birthdays")
    cnt = cursor.fetchone()['cnt']
    if cnt == 0:
        cursor.execute("""
            INSERT INTO birthdays (username, birth_date)
            VALUES (?, ?)
        """, ("Demo_User", today_mm_dd))
        conn.commit()
    conn.close()
