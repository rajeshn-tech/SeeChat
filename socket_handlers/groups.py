import time
from flask import request
from flask_socketio import emit
import database.groups as db_groups
import database.users as db_users
import database.db as db_core

def register_group_and_admin_handlers(socketio, sid_to_user, active_users, broadcast_online_users_fn):
    
    @socketio.on('create_broadcast_group')
    @socketio.on('create_group')
    def handle_create_group(data):
        uname = sid_to_user.get(request.sid)
        group_name = data.get('group_name', '').strip()
        members = data.get('members', [])
        if not uname or not group_name:
            emit('group_action_response', {'success': False, 'message': 'Group name cannot be empty.', 'action': 'create_group'})
            return

        success, msg = db_groups.create_broadcast_group(group_name, uname, members)
        if success:
            groups = db_groups.get_broadcast_groups()
            socketio.emit('broadcast_groups_list', groups)
        emit('group_action_response', {'success': success, 'message': msg, 'action': 'create_group'})

    @socketio.on('add_member_to_group')
    @socketio.on('add_to_group')
    def handle_add_member(data):
        uname = sid_to_user.get(request.sid)
        group_name = data.get('group_name', '').strip()
        target_user = data.get('username', '').strip()
        if not uname or not group_name or not target_user:
            emit('group_action_response', {'success': False, 'message': 'Invalid user or group parameter.', 'action': 'add_member'})
            return

        success, msg = db_groups.add_member_to_group(group_name, target_user)
        if success:
            groups = db_groups.get_broadcast_groups()
            socketio.emit('broadcast_groups_list', groups)
        emit('group_action_response', {'success': success, 'message': msg, 'action': 'add_member'})

    @socketio.on('update_group_members')
    def handle_update_members(data):
        uname = sid_to_user.get(request.sid)
        group_name = data.get('group_name', '').strip()
        members = data.get('members', [])
        if uname and group_name:
            success, msg = db_groups.update_group_members(group_name, members)
            if success:
                groups = db_groups.get_broadcast_groups()
                socketio.emit('broadcast_groups_list', groups)
            emit('group_action_response', {'success': success, 'message': msg, 'action': 'update_members'})

    @socketio.on('rename_broadcast_group')
    def handle_rename_group(data):
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        if old_name and new_name:
            db_groups.rename_broadcast_group(old_name, new_name)
            groups = db_groups.get_broadcast_groups()
            socketio.emit('broadcast_groups_list', groups)

    @socketio.on('delete_broadcast_group')
    def handle_delete_group(data):
        group_name = data.get('group_name')
        if group_name:
            db_groups.delete_broadcast_group(group_name)
            groups = db_groups.get_broadcast_groups()
            socketio.emit('broadcast_groups_list', groups)

    # --- ADMIN CONTROL HANDLERS (BACKEND ROLE AUTHORIZED) ---
    @socketio.on('admin_get_users')
    def handle_admin_get_users():
        uname = sid_to_user.get(request.sid)
        user_info = active_users.get(uname, {})
        if user_info.get('role') != 'admin':
            return
        users = db_users.get_all_registered_users()
        health = {
            'python_server': 'Running',
            'socket_io': 'Connected',
            'sqlite_db': f'Connected ({db_core.get_connection()[1].upper()} Engine)',
            'csv_logger': 'Running',
            'uptime': db_core.get_server_uptime_str(),
            'active_connections': len(active_users)
        }
        emit('admin_users_list', users)
        emit('server_health_data', health)

    @socketio.on('admin_add_user')
    def handle_admin_add_user(data):
        uname = sid_to_user.get(request.sid)
        user_info = active_users.get(uname, {})
        if user_info.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'add_user'})
            return
        
        target_uname = data.get('username', '').strip()
        target_role = data.get('role', 'user')
        if not target_uname:
            emit('admin_action_response', {'success': False, 'message': 'Username cannot be empty.', 'action': 'add_user'})
            return
            
        success, msg = db_users.add_user_by_admin(target_uname, target_role)
        emit('admin_action_response', {'success': success, 'message': msg, 'action': 'add_user'})
        
        if success and broadcast_online_users_fn:
            broadcast_online_users_fn()
            users = db_users.get_all_registered_users()
            emit('admin_users_list', users)

    @socketio.on('admin_delete_user')
    def handle_admin_delete_user(data):
        uname = sid_to_user.get(request.sid)
        user_info = active_users.get(uname, {})
        if user_info.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'delete_user'})
            return
        
        target_uname = data.get('username', '').strip()
        if target_uname == uname:
            emit('admin_action_response', {'success': False, 'message': 'Cannot delete your own active session account.', 'action': 'delete_user'})
            return
            
        if target_uname:
            success, msg = db_users.delete_user_by_admin(target_uname)
            emit('admin_action_response', {'success': success, 'message': msg, 'action': 'delete_user'})
            if success and broadcast_online_users_fn:
                broadcast_online_users_fn()
                users = db_users.get_all_registered_users()
                emit('admin_users_list', users)

    @socketio.on('admin_toggle_user_disabled')
    def handle_admin_toggle_disabled(data):
        uname = sid_to_user.get(request.sid)
        user_info = active_users.get(uname, {})
        if user_info.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'toggle_disabled'})
            return
        
        target_uname = data.get('username', '').strip()
        if target_uname == uname:
            emit('admin_action_response', {'success': False, 'message': 'Cannot disable your own active session account.', 'action': 'toggle_disabled'})
            return
            
        if target_uname:
            success, msg = db_users.toggle_user_disabled(target_uname)
            emit('admin_action_response', {'success': success, 'message': msg, 'action': 'toggle_disabled'})
            if success and broadcast_online_users_fn:
                broadcast_online_users_fn()
                users = db_users.get_all_registered_users()
                emit('admin_users_list', users)

    @socketio.on('admin_toggle_user_role')
    def handle_admin_toggle_role(data):
        uname = sid_to_user.get(request.sid)
        user_info = active_users.get(uname, {})
        if user_info.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'toggle_role'})
            return
        
        target_uname = data.get('username', '').strip()
        target_role = data.get('role')
        if target_uname == uname:
            emit('admin_action_response', {'success': False, 'message': 'Cannot modify role for your own active session account.', 'action': 'toggle_role'})
            return

        if target_uname:
            success, msg = db_users.toggle_user_role(target_uname, target_role)
            emit('admin_action_response', {'success': success, 'message': msg, 'action': 'toggle_role'})
            if success and broadcast_online_users_fn:
                broadcast_online_users_fn()
                users = db_users.get_all_registered_users()
                emit('admin_users_list', users)

    @socketio.on('admin_broadcast_announcement')
    def handle_admin_broadcast(data):
        uname = sid_to_user.get(request.sid)
        if not uname:
            emit('admin_action_response', {'success': False, 'message': 'Authentication required.', 'action': 'broadcast'})
            return

        db_u = db_users.get_user_by_username(uname)
        if not db_u or db_u.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request. Admin role required.', 'action': 'broadcast'})
            return
        
        notice_text = data.get('notice', '').strip()
        if notice_text:
            socketio.emit('receive_studio_announcement', {
                'sender': uname,
                'message': notice_text,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            emit('admin_action_response', {'success': True, 'message': 'Announcement broadcasted successfully to all connected users.', 'action': 'broadcast'})
