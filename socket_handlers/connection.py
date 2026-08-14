import time
import logging
from flask import request
from flask_socketio import emit, join_room, leave_room
from services.auth_service import authenticate_user, verify_jwt_token
import database.users as db_users
import database.groups as db_groups
import database.messages as db_messages

logger = logging.getLogger('seechat.presence')

def register_connection_handlers(socketio, sid_to_user, active_users):
    
    last_broadcast_time = 0.0
    broadcast_pending = False
    
    def broadcast_online_users(immediate=False):
        nonlocal last_broadcast_time, broadcast_pending
        now = time.time()
        
        # Debounce/coalesce presence broadcasts to prevent N x N disconnect storms (min 0.35s interval)
        if not immediate and (now - last_broadcast_time < 0.35):
            if not broadcast_pending:
                broadcast_pending = True
                def delayed_broadcast():
                    time.sleep(0.4)
                    do_broadcast()
                socketio.start_background_task(delayed_broadcast)
            return
            
        do_broadcast()

    def do_broadcast():
        nonlocal last_broadcast_time, broadcast_pending
        broadcast_pending = False
        last_broadcast_time = time.time()
        try:
            users_list = []
            registered_users = db_users.get_all_registered_users()
            for reg_user in registered_users:
                uname = reg_user['username']
                is_online = (uname in active_users) or (uname == 'Demo_User')
                users_list.append({
                    'username': uname,
                    'role': reg_user['role'],
                    'ip_address': reg_user.get('ip_address', '127.0.0.1'),
                    'status': 'online' if is_online else 'offline',
                    'is_disabled': bool(reg_user.get('is_disabled', 0)),
                    'is_online': is_online,
                    'mood_status': reg_user.get('mood_status', 'Available')
                })
            socketio.emit('online_users_list', users_list)
        except Exception as e:
            logger.warning("Presence broadcast emit warning: %s", e)

    @socketio.on('user_login')
    def handle_login(data):
        if not isinstance(data, dict):
            data = {}
            
        authenticated_user = None
        authenticated_role = 'user'
        jwt_token = None

        token = data.get('token')
        if token:
            decoded = verify_jwt_token(token)
            if decoded:
                authenticated_user = decoded['username']
                authenticated_role = decoded['role']
                jwt_token = token
        
        if not authenticated_user:
            username = data.get('username', '').strip() if isinstance(data.get('username'), str) else ''
            password = data.get('password', '').strip() if isinstance(data.get('password'), str) else ''
            
            if not username:
                emit('login_failed', {'error': 'Username is required'})
                return
            
            client_ip = request.remote_addr or '127.0.0.1'
            success, role, message, new_token = authenticate_user(username, password, client_ip)

            if not success:
                emit('login_failed', {'error': message})
                return
                
            authenticated_user = username
            authenticated_role = role
            jwt_token = new_token

        client_ip = request.remote_addr or '127.0.0.1'
        sid_to_user[request.sid] = authenticated_user
        
        # Join user rooms for multi-tab / multi-socket real-time broadcasting
        try:
            join_room(authenticated_user)
            join_room(f"user_{authenticated_user}")
        except Exception:
            pass

        active_users[authenticated_user] = {
            'socket_id': request.sid,
            'ip': client_ip,
            'status': 'online',
            'role': authenticated_role
        }
        
        # Send login success confirmation & initial state
        unread_counts = db_messages.get_unread_counts(authenticated_user)
        user_info = db_users.get_user_by_username(authenticated_user)
        mood_status = user_info.get('mood_status', 'Available') if user_info else 'Available'

        emit('login_success', {
            'username': authenticated_user, 
            'role': authenticated_role, 
            'status': 'online', 
            'token': jwt_token,
            'unread_counts': unread_counts,
            'mood_status': mood_status
        })
        
        broadcast_online_users(immediate=True)
        groups = db_groups.get_broadcast_groups()
        emit('broadcast_groups_list', groups)

    @socketio.on('disconnect')
    def handle_disconnect():
        uname = sid_to_user.get(request.sid)
        if uname:
            try:
                del sid_to_user[request.sid]
            except KeyError:
                pass
            
            remaining_sids = [s for s, u in sid_to_user.items() if u == uname]
            if not remaining_sids and uname in active_users:
                try:
                    del active_users[uname]
                    db_users.update_user_status(uname, '127.0.0.1', 'offline')
                except Exception as e:
                    logger.warning("Disconnect DB update warning for %s: %s", uname, e)
                broadcast_online_users(immediate=False)
                
    return broadcast_online_users
