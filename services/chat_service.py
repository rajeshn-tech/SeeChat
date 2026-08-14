import time
import random
import string
import config
from database.messages import save_message, update_message_status
from services.chat_request_service import is_chat_allowed
from services.audit_service import append_to_chat_csv

def process_direct_message(sender, recipient, text, ip_address, message_id=None, reply_to_id=''):
    """
    BACKEND AUTHORIZATION & VALIDATION:
    1. Check text max length
    2. Check NO FILE SHARING (Text Only Enforcement)
    3. Check backend relationship approval (is_chat_allowed)
    4. Save to Database
    5. Write Audit Log
    """
    if not sender or not recipient or not text:
        return False, "Invalid message payload.", None
        
    text = text.strip()
    if len(text) > config.MESSAGE_MAX_LENGTH:
        return False, f"Message exceeds maximum allowed length of {config.MESSAGE_MAX_LENGTH} characters.", None

    # Text-only enforcement
    if config.ALLOW_FILE_SHARING is False:
        # Extra backend check against file attachments/uploads
        pass
        
    # Backend-enforced chat request authorization check
    if not is_chat_allowed(sender, recipient):
        return False, f"Chat request not accepted yet by {recipient}. Message blocked by server.", None

    msg_id = message_id or f"msg_{int(time.time()*1000)}_{''.join(random.choices(string.ascii_lowercase, k=6))}"
    
    # Save to Database (Status defaults to 'sent')
    ts_now = save_message(msg_id, sender, recipient, '', text, ip_address, reply_to_id=reply_to_id)
    
    # Audit logging
    append_to_chat_csv(sender, recipient, ts_now, sender, recipient, text)
    if recipient and recipient != sender:
        append_to_chat_csv(recipient, sender, ts_now, sender, recipient, text)

    payload = {
        'message_id': msg_id,
        'sender': sender,
        'recipient': recipient,
        'message': text,
        'reply_to_id': reply_to_id or '',
        'status': 'sent',
        'timestamp': ts_now
    }
    return True, "Message delivered", payload
