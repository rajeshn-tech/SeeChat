import time
import sys
import os
import threading
import psutil
import logging
import uuid

logging.getLogger('websocket').setLevel(logging.CRITICAL)
logging.getLogger('engineio').setLevel(logging.CRITICAL)
logging.getLogger('socketio').setLevel(logging.CRITICAL)

try:
    threading.stack_size(256 * 1024)
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import database.db as db_core
import database.users as db_users
import socketio

SERVER_URL = f"http://127.0.0.1:{config.PORT}"

def setup_authorized_test_pairs(target_clients):
    config.AD_AUTH_ENABLED = False
    config.ADMIN_DIRECT_MESSAGE = False
    db_core.init_db()
    db_users.seed_default_users()
    
    conn, db_engine = db_core.get_connection()
    cursor = conn.cursor()
    
    for i in range(target_clients):
        uname = f"LoadUser_{i}"
        cursor.execute("SELECT username FROM users WHERE username = ?", (uname,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, ip_address, status, is_disabled)
                VALUES (?, '', 'user', '127.0.0.1', 'offline', 0)
            """, (uname,))
            
    for i in range(target_clients):
        sender = f"LoadUser_{i}"
        recipient = f"LoadUser_{(i + 1) % target_clients}"
        cursor.execute("""
            INSERT INTO chat_requests (sender, recipient, status)
            VALUES (?, ?, 'accepted')
            ON CONFLICT(sender, recipient) DO UPDATE SET status = 'accepted'
        """, (sender, recipient))
        
    conn.commit()
    conn.close()

def run_single_level_benchmark(target_clients=100, is_sustained=False):
    setup_authorized_test_pairs(target_clients)

    requested = target_clients
    attempted = 0
    connected = 0
    failed = 0
    timeout = 0
    disconnected = 0
    
    messages_attempted = 0
    messages_accepted = 0
    messages_received = 0
    duplicates_received = 0

    sent_msg_ids = set()
    accepted_msg_ids = set()
    received_msg_ids = set()

    delivery_latencies = []
    sent_timestamps = {}
    lock = threading.Lock()

    ram_before = round(psutil.Process(os.getpid()).memory_info().rss / (1024**2), 2)
    cpu_before = psutil.cpu_percent(interval=None)
    start_time = time.time()
    
    clients_map = {}

    def client_worker(user_id):
        nonlocal attempted, connected, failed, timeout, disconnected
        username = f"LoadUser_{user_id}"
        sio = socketio.Client(logger=False, engineio_logger=False)
        
        with lock:
            attempted += 1

        @sio.on('login_success')
        def on_login(data):
            with lock:
                nonlocal connected
                connected += 1

        @sio.on('receive_direct_message')
        def on_receive(data):
            msg_id = data.get('message_id')
            t_recv = time.time()
            with lock:
                if msg_id in received_msg_ids:
                    nonlocal duplicates_received
                    duplicates_received += 1
                else:
                    if msg_id:
                        received_msg_ids.add(msg_id)
                    nonlocal messages_received
                    messages_received += 1
                    if msg_id in sent_timestamps:
                        lat_ms = (t_recv - sent_timestamps[msg_id]) * 1000
                        delivery_latencies.append(lat_ms)

        @sio.on('message_sent_confirm')
        def on_confirm(data):
            msg_id = data.get('message_id')
            with lock:
                if msg_id and msg_id not in accepted_msg_ids:
                    accepted_msg_ids.add(msg_id)
                    nonlocal messages_accepted
                    messages_accepted += 1

        try:
            sio.connect(SERVER_URL, transports=['websocket', 'polling'], wait_timeout=10)
            sio.emit('user_login', {'username': username, 'password': 'nopassword', 'status': 'online'})
            clients_map[user_id] = (sio, username)
        except socketio.exceptions.TimeoutError:
            with lock:
                timeout += 1
        except Exception:
            with lock:
                failed += 1

    threads = []
    stagger_delay = 0.008 if target_clients <= 250 else 0.004
    for i in range(target_clients):
        t = threading.Thread(target=client_worker, args=(i,))
        t.start()
        threads.append(t)
        if i % 50 == 0 and i > 0:
            time.sleep(0.1)
        else:
            time.sleep(stagger_delay)

    for t in threads:
        t.join()

    # Connection settling time
    time.sleep(1.5)

    cpu_peak = psutil.cpu_percent(interval=None)
    ram_peak = round(psutil.Process(os.getpid()).memory_info().rss / (1024**2), 2)

    # Messaging phase with 1-to-1 unique message correlation IDs
    for i, (sio, username) in list(clients_map.items()):
        recipient = f"LoadUser_{(i + 1) % target_clients}"
        msg_id = f"msg_{username}_{recipient}_{uuid.uuid4().hex[:8]}"
        sent_timestamps[msg_id] = time.time()
        
        with lock:
            messages_attempted += 1
            sent_msg_ids.add(msg_id)
            
        try:
            sio.emit('send_direct_message', {
                'message_id': msg_id,
                'sender': username,
                'recipient': recipient,
                'text': f"Strict correlation benchmark payload from {username}"
            })
        except Exception:
            pass
        time.sleep(0.002)

    # Delivery settling time before socket disconnect
    hold_time = 4.0 if is_sustained else 2.5
    time.sleep(hold_time)

    for i, (sio, username) in list(clients_map.items()):
        try:
            sio.disconnect()
            with lock:
                disconnected += 1
        except Exception:
            pass

    elapsed = round(time.time() - start_time, 2)
    ram_after = round(psutil.Process(os.getpid()).memory_info().rss / (1024**2), 2)
    
    messages_lost = messages_accepted - messages_received
    if messages_lost < 0: messages_lost = 0

    delivery_latencies.sort()
    avg_lat = round(sum(delivery_latencies) / len(delivery_latencies), 2) if delivery_latencies else 'NOT MEASURED'
    min_lat = round(min(delivery_latencies), 2) if delivery_latencies else 'NOT MEASURED'
    max_lat = round(max(delivery_latencies), 2) if delivery_latencies else 'NOT MEASURED'
    
    p50_idx = int(len(delivery_latencies) * 0.50)
    p95_idx = int(len(delivery_latencies) * 0.95)
    p99_idx = int(len(delivery_latencies) * 0.99)
    p50_lat = round(delivery_latencies[p50_idx], 2) if delivery_latencies and p50_idx < len(delivery_latencies) else 'NOT MEASURED'
    p95_lat = round(delivery_latencies[p95_idx], 2) if delivery_latencies and p95_idx < len(delivery_latencies) else 'NOT MEASURED'
    p99_lat = round(delivery_latencies[p99_idx], 2) if delivery_latencies and p99_idx < len(delivery_latencies) else 'NOT MEASURED'

    if failed == 0 and timeout == 0 and connected == target_clients and messages_lost == 0 and duplicates_received == 0:
        grade = "HEALTHY"
    elif connected >= target_clients * 0.8 and messages_lost == 0:
        grade = "PASS WITH LIMITED HEADROOM"
    elif connected > 0:
        grade = "BOTTLENECK"
    else:
        grade = "FAIL"

    res = {
        'target_clients': target_clients,
        'requested': requested,
        'attempted': attempted,
        'connected': connected,
        'failed': failed,
        'timeout': timeout,
        'disconnected': disconnected,
        'messages_attempted': messages_attempted,
        'messages_accepted': messages_accepted,
        'messages_received': messages_received,
        'messages_lost': messages_lost,
        'duplicates': duplicates_received,
        'avg_lat': avg_lat,
        'min_lat': min_lat,
        'max_lat': max_lat,
        'p50_lat': p50_lat,
        'p95_lat': p95_lat,
        'p99_lat': p99_lat,
        'ram_before': ram_before,
        'ram_peak': ram_peak,
        'ram_after': ram_after,
        'cpu_peak': cpu_peak,
        'elapsed': elapsed,
        'grade': grade
    }

    print(f"==================================================================")
    print(f"   RESULTS FOR {target_clients} CONCURRENT CLIENT BENCHMARK")
    print(f"==================================================================")
    print(f" Requested / Attempted:  {requested} / {attempted}")
    print(f" Connected Sockets:     {connected}")
    print(f" Failed / Timeouts:      {failed} / {timeout}")
    print(f" Disconnected Cleanly:  {disconnected}")
    print(f" Messages Attempted:    {messages_attempted}")
    print(f" Server-Accepted:       {messages_accepted}")
    print(f" Recipient-Received:    {messages_received}")
    print(f" Messages Lost:         {messages_lost}")
    print(f" Duplicates Received:   {duplicates_received}")
    print(f" Latencies (ms):        Avg: {avg_lat} | P50: {p50_lat} | P95: {p95_lat} | P99: {p99_lat} | Max: {max_lat}")
    print(f" RAM Peak / CPU Peak:   {ram_peak} MB / {cpu_peak}%")
    print(f" Duration / Grade:      {elapsed}s | {grade}")
    print(f"==================================================================\n")
    
    return res

if __name__ == '__main__':
    target = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 100
    run_single_level_benchmark(target_clients=target, is_sustained=False)
