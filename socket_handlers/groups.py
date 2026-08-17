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

    @socketio.on('admin_get_birthdays')
    def handle_admin_get_birthdays():
        uname = sid_to_user.get(request.sid)
        if not uname:
            return
        import database.birthdays as db_birthdays
        bday_list = db_birthdays.get_all_birthdays()
        emit('admin_birthdays_list', bday_list)

    @socketio.on('admin_set_birthday')
    def handle_admin_set_birthday(data):
        uname = sid_to_user.get(request.sid)
        db_u = db_users.get_user_by_username(uname) if uname else None
        if not db_u or db_u.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'set_birthday'})
            return

        target_uname = data.get('username', '').strip()
        birth_date = data.get('birth_date', '').strip()
        import database.birthdays as db_birthdays
        ok, msg = db_birthdays.set_user_birthday(target_uname, birth_date)
        emit('admin_action_response', {'success': ok, 'message': msg, 'action': 'set_birthday'})
        if ok:
            bday_list = db_birthdays.get_all_birthdays()
            socketio.emit('admin_birthdays_list', bday_list)

    @socketio.on('admin_delete_birthday')
    def handle_admin_delete_birthday(data):
        uname = sid_to_user.get(request.sid)
        db_u = db_users.get_user_by_username(uname) if uname else None
        if not db_u or db_u.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'delete_birthday'})
            return

        target_uname = data.get('username', '').strip()
        import database.birthdays as db_birthdays
        ok, msg = db_birthdays.delete_user_birthday(target_uname)
        emit('admin_action_response', {'success': ok, 'message': msg, 'action': 'delete_birthday'})
        if ok:
            bday_list = db_birthdays.get_all_birthdays()
            socketio.emit('admin_birthdays_list', bday_list)

    @socketio.on('admin_broadcast_birthdays')
    def handle_admin_broadcast_birthdays():
        uname = sid_to_user.get(request.sid)
        db_u = db_users.get_user_by_username(uname) if uname else None
        if not db_u or db_u.get('role') != 'admin':
            emit('admin_action_response', {'success': False, 'message': 'Unauthorized admin request.', 'action': 'broadcast_birthdays'})
            return

        import database.birthdays as db_birthdays
        today_bday_list = db_birthdays.get_today_birthdays()
        if today_bday_list:
            bday_names = [b['username'] for b in today_bday_list]
            socketio.emit('receive_birthday_announcement', {
                'birthday_users': bday_names,
                'message': f"🎉 Today is {', '.join(bday_names)}'s Birthday! Wish them a Happy Birthday! 🎂🎈",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            emit('admin_action_response', {'success': True, 'message': f"Broadcasted today's birthdays ({', '.join(bday_names)}) to all connected users!", 'action': 'broadcast_birthdays'})
        else:
            emit('admin_action_response', {'success': False, 'message': "No birthdays found for today's date.", 'action': 'broadcast_birthdays'})

    @socketio.on('send_birthday_wish')
    def handle_send_birthday_wish(data):
        sender = sid_to_user.get(request.sid)
        if not sender:
            return

        bday_user = data.get('birthday_user', '').strip()
        wish_text = data.get('wish_text', '').strip()

        if not bday_user or not wish_text:
            emit('birthday_wish_sent_response', {'success': False, 'message': 'Invalid wish selection.'})
            return

        import database.birthdays as db_birthdays
        ok, wish_id = db_birthdays.add_birthday_wish(bday_user, sender, wish_text)
        if ok:
            emit('birthday_wish_sent_response', {'success': True, 'message': f'Professional birthday wish delivered to {bday_user}! 🎉'})
            # Notify birthday user in real-time
            wishes = db_birthdays.get_wishes_for_user(bday_user)
            socketio.emit('receive_birthday_wish_notification', {
                'sender': sender,
                'wish_text': wish_text,
                'wishes': wishes
            }, room=f"user_{bday_user}")
        else:
            emit('birthday_wish_sent_response', {'success': False, 'message': 'Failed to deliver wish.'})

    @socketio.on('get_my_birthday_wishes')
    def handle_get_my_birthday_wishes():
        uname = sid_to_user.get(request.sid)
        if not uname:
            return
        import database.birthdays as db_birthdays
        wishes = db_birthdays.get_wishes_for_user(uname)
        emit('my_birthday_wishes_list', {'wishes': wishes})

    @socketio.on('send_birthday_thank_you')
    def handle_send_birthday_thank_you(data):
        uname = sid_to_user.get(request.sid)
        if not uname:
            return

        wish_id = data.get('wish_id')
        thank_you_text = data.get('thank_you_text', '').strip()

        if not wish_id or not thank_you_text:
            return

        import database.birthdays as db_birthdays
        ok, wishing_sender, bday_user = db_birthdays.send_thank_you_for_wish(wish_id, thank_you_text)
        if ok and wishing_sender:
            emit('birthday_thank_you_sent_response', {'success': True, 'message': f'Thank-you response sent to {wishing_sender}! 🙏'})
            # Notify wish sender in real-time
            socketio.emit('receive_birthday_thank_you_notification', {
                'birthday_user': uname,
                'thank_you_text': thank_you_text,
                'timestamp': time.strftime('%H:%M')
            }, room=f"user_{wishing_sender}")
