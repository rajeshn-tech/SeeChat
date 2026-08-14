import sqlite3
import os
import sys
import config

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'data', 'seechat_audit.db')

def confirm_reset():
    # Production Safety Guard
    if os.environ.get('SEECHAT_ALLOW_DB_RESET', 'false').lower() == 'true' or '--force' in sys.argv:
        return True
    
    if sys.stdin.isatty():
        print("[WARNING] You are about to reset local database password hashes!")
        confirm = input("Type 'CONFIRM' to proceed with reset: ").strip()
        return confirm == 'CONFIRM'
    
    print("[ERROR] Database reset requires '--force' flag or SEECHAT_ALLOW_DB_RESET=true in non-interactive mode.")
    return False

if __name__ == '__main__':
    if not confirm_reset():
        print("Operation cancelled. Database untouched.")
        sys.exit(1)
        
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ''")
        conn.commit()
        conn.close()
        print("[SUCCESS] Database password hashes reset successfully.")
    else:
        print("Database file not found.")
