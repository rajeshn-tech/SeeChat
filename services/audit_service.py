import os
import csv
import config

def sanitize_csv_field(val):
    """
    CSV Formula Injection Protection:
    Prevents spreadsheet formula execution when CSV logs are opened in Excel/Calc.
    Strips leading whitespace/tabs before checking if string begins with =, +, -, @.
    If so, prefixes with a single quote.
    """
    if isinstance(val, str):
        stripped = val.lstrip()
        if stripped.startswith(('=', '+', '-', '@')):
            return "'" + val
    return val

def append_to_chat_csv(folder_user, partner_name, timestamp, sender, recipient, message):
    if not config.AUDIT_LOGGING:
        return
    try:
        user_folder = os.path.join(config.CHAT_LOGS_DIR, folder_user)
        os.makedirs(user_folder, exist_ok=True)
        
        safe_partner = partner_name.replace(' ', '_').replace('/', '_')
        file_path = os.path.join(user_folder, f"chat_with_{safe_partner}.csv")
        file_exists = os.path.exists(file_path)
        
        # Sanitize CSV formula injection triggers
        safe_sender = sanitize_csv_field(sender)
        safe_recipient = sanitize_csv_field(recipient)
        safe_message = sanitize_csv_field(message)
        
        with open(file_path, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Date & Time', 'Sender Name', 'Receiver / Group', 'Message Content'])
            writer.writerow([timestamp, safe_sender, safe_recipient, safe_message])
    except Exception as e:
        import logging
        logging.getLogger('seechat.audit').warning("CSV audit logging write warning: %s", e)
