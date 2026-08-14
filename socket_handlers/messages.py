import time
import random
import string
import config

from flask import request
from flask_socketio import emit

from services.chat_service import process_direct_message
import database.messages as db_messages
import database.users as db_users


user_msg_timestamps = {}


def is_rate_limited(username):
    now = time.time()
    timestamps = user_msg_timestamps.get(username, [])
    timestamps = [t for t in timestamps if now - t < 1.0]

    if len(timestamps) >= config.MAX_MESSAGES_PER_SECOND:
        user_msg_timestamps[username] = timestamps
        return True

    timestamps.append(now)
    user_msg_timestamps[username] = timestamps
    return False


def register_message_handlers(socketio, sid_to_user, active_users):

    @socketio.on('send_direct_message')
    def handle_direct_message(data):
        sender = sid_to_user.get(request.sid)
        if not sender:
            emit('message_send_failed', {'error': 'Authentication required.'})
            return

        recipient = data.get('recipient')
        text = data.get('text', '').strip()

        if not recipient or not text:
            return

        if is_rate_limited(sender):
            emit('message_send_failed', {
                'error': 'Rate limit exceeded (max 10 msgs/sec). Please slow down.',
                'recipient': recipient
            })
            return

        sid_to_user[request.sid] = sender
        if sender not in active_users:
            active_users[sender] = {
                'socket_id': request.sid,
                'ip': request.remote_addr or '127.0.0.1',
                'status': 'online',
                'role': 'admin' if 'admin' in sender.lower() else 'user'
            }

        client_ip = request.remote_addr or '127.0.0.1'
        msg_id = data.get('message_id')
        reply_to_id = data.get('reply_to_id', '')

        # Backend payload validation & chat-request authorization check
        success, err_msg, msg_payload = process_direct_message(
            sender, recipient, text, client_ip, msg_id, reply_to_id=reply_to_id
        )

        if not success:
            emit('message_send_failed', {'error': err_msg, 'recipient': recipient})
            return

        # Attach reply_preview if reply_to_id specified
        if reply_to_id:
            ref_msg = db_messages.get_message_by_id(reply_to_id)
            if ref_msg:
                msg_payload['reply_preview'] = {
                    'message_id': ref_msg['message_id'],
                    'sender': ref_msg['sender'],
                    'message': ref_msg['message']
                }

        # Message successfully accepted/saved by server (Initial Status: 'sent')
        msg_payload['status'] = 'sent'
        emit('message_sent_confirm', msg_payload)

        # Deliver to intended recipient (all active sockets/tabs for recipient)
        socketio.emit('receive_direct_message', msg_payload, room=recipient)
        socketio.emit('receive_direct_message', msg_payload, room=f"user_{recipient}")
        recipient_user = active_users.get(recipient)
        if recipient_user and recipient_user.get('socket_id'):
            socketio.emit('receive_direct_message', msg_payload, room=recipient_user['socket_id'])

    @socketio.on('toggle_message_reaction')
    def handle_toggle_reaction(data):
        username = sid_to_user.get(request.sid)
        if not username:
            return

        msg_id = data.get('message_id')
        emoji = data.get('emoji')

        if not msg_id or not emoji:
            return

        reactions = db_messages.toggle_reaction(msg_id, username, emoji)

        # Fetch message to determine recipients to notify
        target_msg = db_messages.get_message_by_id(msg_id)
        if target_msg:
            reaction_data = {'message_id': msg_id, 'reactions': reactions}
            s = target_msg['sender']
            r = target_msg['recipient']

            socketio.emit('message_reactions_updated', reaction_data, room=s)
            socketio.emit('message_reactions_updated', reaction_data, room=f"user_{s}")
            if r != s:
                socketio.emit('message_reactions_updated', reaction_data, room=r)
                socketio.emit('message_reactions_updated', reaction_data, room=f"user_{r}")

    @socketio.on('edit_message')
    def handle_edit_message(data):
        username = sid_to_user.get(request.sid)
        if not username:
            emit('message_send_failed', {'error': 'Authentication required.'})
            return

        msg_id = data.get('message_id')
        new_text = data.get('new_text', '').strip()

        if not msg_id or not new_text:
            return

        if len(new_text) > config.MESSAGE_MAX_LENGTH:
            emit('message_send_failed', {'error': f'Message exceeds maximum allowed length of {config.MESSAGE_MAX_LENGTH} characters.'})
            return

        ok, err_msg, updated_msg = db_messages.edit_message(msg_id, username, new_text)
        if not ok:
            emit('message_send_failed', {'error': err_msg})
            return

        target_msg = db_messages.get_message_by_id(msg_id)
        if target_msg:
            edit_event_data = {
                'message_id': msg_id,
                'new_text': new_text,
                'is_edited': True,
                'edited_at': updated_msg.get('edited_at') if updated_msg else ''
            }
            s = target_msg['sender']
            r = target_msg['recipient']

            socketio.emit('message_edited', edit_event_data, room=s)
            socketio.emit('message_edited', edit_event_data, room=f"user_{s}")
            if r != s:
                socketio.emit('message_edited', edit_event_data, room=r)
                socketio.emit('message_edited', edit_event_data, room=f"user_{r}")

    @socketio.on('delete_message')
    def handle_delete_message(data):
        username = sid_to_user.get(request.sid)
        if not username:
            emit('message_send_failed', {'error': 'Authentication required.'})
            return

        msg_id = data.get('message_id')
        if not msg_id:
            return

        target_msg = db_messages.get_message_by_id(msg_id)
        if not target_msg:
            emit('message_send_failed', {'error': 'Message not found.'})
            return

        ok, err_msg, deleted_msg = db_messages.delete_message(msg_id, username)
        if not ok:
            emit('message_send_failed', {'error': err_msg})
            return

        delete_event_data = {
            'message_id': msg_id,
            'is_deleted': True,
            'deleted_at': deleted_msg.get('deleted_at') if deleted_msg else ''
        }
        s = target_msg['sender']
        r = target_msg['recipient']

        socketio.emit('message_deleted', delete_event_data, room=s)
        socketio.emit('message_deleted', delete_event_data, room=f"user_{s}")
        if r != s:
            socketio.emit('message_deleted', delete_event_data, room=r)
            socketio.emit('message_deleted', delete_event_data, room=f"user_{r}")

    @socketio.on('message_delivered_ack')
    def handle_delivered_ack(data):
        recipient = sid_to_user.get(request.sid)
        if not recipient:
            return

        msg_id = data.get('message_id')
        if not msg_id:
            return

        ok, sender, intended_recipient, message_id = db_messages.update_message_status_delivered(msg_id, recipient)
        if ok and sender:
            status_payload = {
                'message_id': message_id,
                'status': 'delivered',
                'recipient': recipient
            }
            socketio.emit('message_status_updated', status_payload, room=sender)
            socketio.emit('message_status_updated', status_payload, room=f"user_{sender}")
            s_user = active_users.get(sender)
            if s_user and s_user.get('socket_id'):
                socketio.emit('message_status_updated', status_payload, room=s_user['socket_id'])

    @socketio.on('mark_conversation_read')
    def handle_mark_read(data):
        recipient = sid_to_user.get(request.sid)
        target_sender = data.get('targetUser')

        if not recipient or not target_sender:
            return

        updated_ids, sender, intended_recipient = db_messages.mark_messages_as_read(target_sender, recipient)
        if updated_ids:
            read_payload = {
                'reader': recipient,
                'message_ids': updated_ids
            }
            # Inform sender in real time across all active sockets/tabs
            socketio.emit('messages_marked_read', read_payload, room=target_sender)
            socketio.emit('messages_marked_read', read_payload, room=f"user_{target_sender}")
            s_user = active_users.get(target_sender)
            if s_user and s_user.get('socket_id'):
                socketio.emit('messages_marked_read', read_payload, room=s_user['socket_id'])

            # Sync unread/read state back to recipient sockets/tabs as well
            socketio.emit('messages_marked_read', read_payload, room=recipient)
            socketio.emit('messages_marked_read', read_payload, room=f"user_{recipient}")

    @socketio.on('typing_start')
    def handle_typing_start(data):
        sender = sid_to_user.get(request.sid)
        recipient = data.get('recipient')
        if sender and recipient:
            socketio.emit('user_typing', {'sender': sender}, room=recipient)
            socketio.emit('user_typing', {'sender': sender}, room=f"user_{recipient}")

    @socketio.on('typing_stop')
    def handle_typing_stop(data):
        sender = sid_to_user.get(request.sid)
        recipient = data.get('recipient')
        if sender and recipient:
            socketio.emit('user_stop_typing', {'sender': sender}, room=recipient)
            socketio.emit('user_stop_typing', {'sender': sender}, room=f"user_{recipient}")

    @socketio.on('send_broadcast_message')
    def handle_broadcast_message(data):
        sender = sid_to_user.get(request.sid)
        if not sender:
            emit('message_send_failed', {'error': 'Authentication required.'})
            return

        group_name = data.get('group_name')
        members = data.get('members', [])
        text = data.get('text', '').strip()

        if not members or not text:
            return

        if is_rate_limited(sender):
            emit('message_send_failed', {
                'error': 'Rate limit exceeded (max 10 msgs/sec). Please slow down.',
                'recipient': group_name
            })
            return

        client_ip = request.remote_addr or '127.0.0.1'
        base_msg_id = data.get('message_id') or f"bcast_{int(time.time() * 1000)}_{''.join(random.choices(string.ascii_lowercase, k=6))}"

        for member in members:
            if member == sender:
                continue

            indiv_msg_id = f"{base_msg_id}_{member}"
            db_messages.save_message(indiv_msg_id, sender, member, group_name, text, client_ip)

            target_user = active_users.get(member)
            if target_user and target_user.get('socket_id'):
                socketio.emit('receive_direct_message', {
                    'message_id': indiv_msg_id,
                    'sender': sender,
                    'recipient': member,
                    'is_broadcast': True,
                    'broadcast_group': group_name,
                    'message': text,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'sent'
                }, room=target_user['socket_id'])

        emit('broadcast_sent_confirm', {
            'group_name': group_name,
            'baseMsgId': base_msg_id,
            'text': text,
            'total_members': len(members),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    @socketio.on('get_chat_history')
    def handle_get_history(data):
        uname = sid_to_user.get(request.sid)
        target_user = data.get('targetUser')

        if uname and target_user:
            history = db_messages.get_chat_history(uname, target_user)
            # Unread count check
            unread_counts = db_messages.get_unread_counts(uname)
            emit('chat_history', {
                'targetUser': target_user,
                'history': history,
                'unread_counts': unread_counts
            })

    @socketio.on('clear_chat_history')
    def handle_clear_history(data):
        uname = sid_to_user.get(request.sid)
        target = data.get('target')

        if uname and target:
            db_messages.clear_chat_with_target(uname, target)
            emit('chat_cleared', {'target': target})