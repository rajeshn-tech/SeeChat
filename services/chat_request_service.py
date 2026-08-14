from database.chat_requests import get_chat_request_status, send_chat_request, respond_chat_request

def is_chat_allowed(sender, recipient):
    """
    CRITICAL SECURITY CHECK:
    Verifies on the backend whether User A has an ACCEPTED relationship with User B
    before allowing any direct message to be saved or delivered.
    """
    if sender == recipient:
        return True
    
    status = get_chat_request_status(sender, recipient)
    return status == 'ACCEPTED'

def request_chat_permission(sender, recipient):
    if sender == recipient:
        return True, 'ACCEPTED'
    return send_chat_request(sender, recipient)

def process_chat_request_response(user, partner, action):
    return respond_chat_request(user, partner, action)
