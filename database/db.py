import sqlite3
import os
import time
import config

os.makedirs(config.DB_DIR, exist_ok=True)
os.makedirs(config.CHAT_LOGS_DIR, exist_ok=True)
os.makedirs(config.LOGS_DIR, exist_ok=True)

DB_PATH = os.path.join(config.DB_DIR, 'seechat_audit.db')
SERVER_START_TIME = time.time()

def get_connection():
    if config.DATABASE_TYPE == 'postgresql' and config.DATABASE_URL:
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            return conn, 'postgresql'
        except Exception as e:
            print(f"[WARN] PostgreSQL connection failed ({e}), falling back to SQLite WAL mode.")
    
    conn = sqlite3.connect(DB_PATH, timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

def init_db():
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    if db_engine == 'sqlite':
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 60000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                ip_address TEXT,
                status TEXT DEFAULT 'online',
                is_disabled INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mood_status TEXT DEFAULT 'Available'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                sender TEXT,
                recipient TEXT,
                broadcast_group TEXT DEFAULT '',
                message TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                seen_at TIMESTAMP,
                reaction TEXT DEFAULT '',
                reply_to_id TEXT DEFAULT '',
                is_edited INTEGER DEFAULT 0,
                edited_at TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                username TEXT NOT NULL,
                emoji TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, username)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                revision_number INTEGER DEFAULT 1,
                previous_text TEXT NOT NULL,
                new_text TEXT NOT NULL,
                edited_by TEXT NOT NULL,
                edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_deletes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                original_message TEXT NOT NULL,
                deleted_by TEXT NOT NULL,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                recipient TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sender, recipient)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE,
                created_by TEXT,
                members TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_chat_clears (
                username TEXT NOT NULL,
                target TEXT NOT NULL,
                cleared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (username, target)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                birth_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS birthday_wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birthday_user TEXT NOT NULL,
                sender TEXT NOT NULL,
                wish_text TEXT NOT NULL,
                thank_you_text TEXT DEFAULT '',
                thank_you_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Safely migrate existing tables if columns missing
        cursor.execute("PRAGMA table_info(users);")
        user_cols = [r['name'] for r in cursor.fetchall()]
        if 'mood_status' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN mood_status TEXT DEFAULT 'Available';")
            
        cursor.execute("PRAGMA table_info(messages);")
        msg_cols = [r['name'] for r in cursor.fetchall()]
        if 'reaction' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN reaction TEXT DEFAULT '';")
        if 'reply_to_id' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN reply_to_id TEXT DEFAULT '';")
        if 'is_edited' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_edited INTEGER DEFAULT 0;")
        if 'edited_at' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN edited_at TIMESTAMP;")
        if 'is_deleted' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_deleted INTEGER DEFAULT 0;")
        if 'deleted_at' not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN deleted_at TIMESTAMP;")

    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(100) PRIMARY KEY,
                password_hash VARCHAR(255) DEFAULT '',
                role VARCHAR(20) DEFAULT 'user',
                ip_address VARCHAR(50),
                status VARCHAR(20) DEFAULT 'online',
                is_disabled INT DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mood_status VARCHAR(50) DEFAULT 'Available'
            );
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR(100) UNIQUE,
                sender VARCHAR(100),
                recipient VARCHAR(100),
                broadcast_group VARCHAR(100) DEFAULT '',
                message TEXT,
                ip_address VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'sent',
                seen_at TIMESTAMP,
                reaction VARCHAR(20) DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS chat_requests (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(100),
                recipient VARCHAR(100),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sender, recipient)
            );
            CREATE TABLE IF NOT EXISTS broadcast_groups (
                id SERIAL PRIMARY KEY,
                group_name VARCHAR(100) UNIQUE,
                created_by VARCHAR(100),
                members TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_chat_clears (
                username VARCHAR(100) NOT NULL,
                target VARCHAR(100) NOT NULL,
                cleared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (username, target)
            );
        """)
    
    conn.commit()
    conn.close()

def get_server_uptime_str():
    uptime_sec = int(time.time() - SERVER_START_TIME)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    mins = (uptime_sec % 3600) // 60
    return f"{days}d {hours}h {mins}m" if days > 0 else f"{hours}h {mins}m"
