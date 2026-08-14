import json
from database.db import get_connection

def create_broadcast_group(group_name, created_by, members):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM broadcast_groups WHERE group_name = ?", (group_name,))
    if cursor.fetchone():
        conn.close()
        return False, f"Group '{group_name}' already exists."
        
    if created_by and created_by not in members:
        members.append(created_by)
        
    members_json = json.dumps(members)
    cursor.execute("""
        INSERT INTO broadcast_groups (group_name, created_by, members)
        VALUES (?, ?, ?)
    """, (group_name, created_by, members_json))
    conn.commit()
    conn.close()
    return True, f"Group '{group_name}' created successfully."

def add_member_to_group(group_name, username):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT members FROM broadcast_groups WHERE group_name = ?", (group_name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, f"Group '{group_name}' does not exist."
        
    try:
        members = json.loads(row['members'] or '[]')
    except Exception:
        members = []
        
    if username in members:
        conn.close()
        return False, f"User '{username}' is already in group '{group_name}'."
        
    members.append(username)
    members_json = json.dumps(members)
    cursor.execute("UPDATE broadcast_groups SET members = ? WHERE group_name = ?", (members_json, group_name))
    conn.commit()
    conn.close()
    return True, f"User '{username}' added to group '{group_name}'."

def update_group_members(group_name, members):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    members_json = json.dumps(members)
    cursor.execute("UPDATE broadcast_groups SET members = ? WHERE group_name = ?", (members_json, group_name))
    conn.commit()
    conn.close()
    return True, f"Group '{group_name}' members updated."

def rename_broadcast_group(old_name, new_name):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE broadcast_groups SET group_name = ? WHERE group_name = ?", (new_name, old_name))
    conn.commit()
    conn.close()
    return True, f"Group renamed to '{new_name}'."

def delete_broadcast_group(group_name):
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM broadcast_groups WHERE group_name = ?", (group_name,))
    conn.commit()
    conn.close()
    return True, f"Group '{group_name}' deleted."

def get_broadcast_groups():
    conn, db_engine = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM broadcast_groups ORDER BY created_at DESC")
    rows = []
    for r in cursor.fetchall():
        row_dict = dict(r)
        try:
            row_dict['members'] = json.loads(row_dict['members'] or '[]')
        except Exception:
            row_dict['members'] = []
        rows.append(row_dict)
    conn.close()
    return rows
