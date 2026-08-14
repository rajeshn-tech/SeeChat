import time
from flask import request
from flask_socketio import emit
from services.chat_request_service import get_chat_request_status, request_chat_permission, process_chat_request_response

def register_chat_request_handlers(socketio, sid_to_user, active_users):
    
    @socketio.on('get_chat_request_status')
    def handle_get_request_status(data):
        uname = sid_to_user.get(request.sid)
        target_user = data.get('targetUser')
        if uname and target_user:
            status_val = get_chat_request_status(uname, target_user)
            emit('chat_request_status_result', {'targetUser': target_user, 'status': status_val.lower()})

    @socketio.on('send_chat_request')
    def handle_send_chat_request(data):
        sender = sid_to_user.get(request.sid)
        recipient = data.get('recipient')
        if not sender or not recipient:
            return
            
        success, status_str = request_chat_permission(sender, recipient)
        emit('chat_request_status_result', {'targetUser': recipient, 'status': 'pending_out'})
        
        recipient_user = active_users.get(recipient)
        if recipient_user:
            socketio.emit('incoming_chat_request', {
                'sender': sender,
                'recipient': recipient,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, room=recipient_user['socket_id'])

    @socketio.on('respond_chat_request')
    def handle_respond_chat_request(data):
        user = sid_to_user.get(request.sid)
        partner = data.get('partner')
        action = data.get('action')
        
        if not user or not partner or not action:
            return
            
        success, status_val = process_chat_request_response(user, partner, action)
        
        emit('chat_request_status_result', {'targetUser': partner, 'status': 'accepted' if action == 'accept' else 'none'})
        
        partner_user = active_users.get(partner)
        if partner_user:
            socketio.emit('chat_request_responded', {
                'responder': user,
                'partner': partner,
                'action': action,
                'status': 'accepted' if action == 'accept' else 'none'
            }, room=partner_user['socket_id'])
