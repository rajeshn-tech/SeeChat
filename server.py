try:
    from gevent import monkey
    monkey.patch_all(logging=False)
    ASYNC_MODE = 'gevent'
except Exception:
    ASYNC_MODE = 'threading'

import os
import logging
import config
from flask import Flask, send_from_directory
from flask_socketio import SocketIO

import database.db as db_core
import database.users as db_users
import database.birthdays as db_birthdays
import generate_ssl

from socket_handlers.connection import register_connection_handlers
from socket_handlers.messages import register_message_handlers
from socket_handlers.chat_requests import register_chat_request_handlers
from socket_handlers.presence import register_presence_handlers
from socket_handlers.groups import register_group_and_admin_handlers

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder='client', static_url_path='')
app.config['SECRET_KEY'] = config.SECRET_KEY

socketio = SocketIO(app, cors_allowed_origins="*", async_mode=ASYNC_MODE)

sid_to_user = {}     # socket.id -> username
active_users = {}    # username -> { socket_id, ip, status, role }

# Route Handlers
@app.route('/')
def index():
    return send_from_directory('client', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('client', path)

# Initialize Database Schema & Seed Default Users & Sample Birthdays
db_core.init_db()
db_users.seed_default_users()
db_birthdays.seed_default_birthdays()

# Register Modular Socket.IO Handlers
broadcast_online_users_fn = register_connection_handlers(socketio, sid_to_user, active_users)
register_message_handlers(socketio, sid_to_user, active_users)
register_chat_request_handlers(socketio, sid_to_user, active_users)
register_presence_handlers(socketio, sid_to_user, active_users, broadcast_online_users_fn)
register_group_and_admin_handlers(socketio, sid_to_user, active_users, broadcast_online_users_fn)

if __name__ == '__main__':
    cert_path, key_path = generate_ssl.generate_self_signed_cert('cert.pem', 'key.pem')
    protocol = "https" if config.USE_SSL else "http"
    
    print("==================================================================")
    print(f"        {config.APP_NAME.upper()} - ENTERPRISE STUDIO MESSENGER SERVER       ")
    print("==================================================================")
    print(" Status:          LIVE & READY FOR DEMO")
    print(f" Branding:        {config.BRANDING_NAME}")
    print(f" Async Worker:    {ASYNC_MODE.upper()} High-Concurrency Engine")
    print(f" AD Auth Mode:    {'ENABLED' if config.AD_AUTH_ENABLED else 'DISABLED (Development Mode Active)'}")
    if not config.AD_AUTH_ENABLED:
        print(" [DIAGNOSTIC WARNING] SeeChat is running with Development Authentication.")
        print(" Active Directory authentication is disabled (AD_AUTH_ENABLED = False).")
    print(f" Security:        JWT Signed Tokens (HS256 Encryption)")
    print(f" Protocol:        {protocol.upper()} Server Active")
    print(f" Studio URL:      {protocol}://seechat:{config.PORT}")
    print(f" Localhost URL:   {protocol}://127.0.0.1:{config.PORT}")
    print(f" Server Port:     {config.PORT} (Internal Port Preserved)")
    print(f" Audit Log Path:  {os.path.abspath(config.CHAT_LOGS_DIR)}")
    print("==================================================================")
    print(" Listening for Workstation Connections...\n")
    
    ssl_context = (cert_path, key_path) if config.USE_SSL else None
    if ssl_context:
        socketio.run(app, host='0.0.0.0', port=config.PORT, ssl_context=ssl_context, debug=False)
    else:
        socketio.run(app, host='0.0.0.0', port=config.PORT, debug=False)
