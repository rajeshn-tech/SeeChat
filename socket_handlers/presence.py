from flask import request
import database.users as db_users

def register_presence_handlers(socketio, sid_to_user, active_users, broadcast_online_users_fn):
    
    @socketio.on('update_status')
    def handle_status(data):
        uname = sid_to_user.get(request.sid)
        if uname and uname in active_users:
            new_status = data.get('status', 'online')
            active_users[uname]['status'] = new_status
            db_users.update_user_status(uname, active_users[uname]['ip'], new_status)
            if broadcast_online_users_fn:
                broadcast_online_users_fn()

    @socketio.on('update_mood_status')
    def handle_mood_status(data):
        uname = sid_to_user.get(request.sid)
        if uname and uname in active_users:
            mood_status = data.get('mood_status', 'Available')
            db_users.update_user_mood_status(uname, mood_status)
            if broadcast_online_users_fn:
                broadcast_online_users_fn(immediate=True)
