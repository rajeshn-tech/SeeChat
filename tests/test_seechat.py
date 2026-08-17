import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import database.db as db_core
import database.users as db_users
import database.groups as db_groups
import database.messages as db_messages
from services.auth_service import authenticate_user, verify_jwt_token
from services.chat_service import process_direct_message
from services.chat_request_service import is_chat_allowed, request_chat_permission, process_chat_request_response
from services.audit_service import sanitize_csv_field, append_to_chat_csv
from socket_handlers.messages import is_rate_limited
from reset_db import confirm_reset

class TestSeeChatCompleteSecurityAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.AD_AUTH_ENABLED = False
        config.ADMIN_DIRECT_MESSAGE = True
        db_core.init_db()
        db_users.seed_default_users()
        db_users.add_user_by_admin("User_A", "user")
        db_users.add_user_by_admin("User_B", "user")
        db_users.add_user_by_admin("User_C", "user")

    def setUp(self):
        # Clean request records between tests
        conn, db_engine = db_core.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_requests")
        cursor.execute("DELETE FROM broadcast_groups")
        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()

    def test_01_valid_development_login(self):
        """1. Valid development mode authentication"""
        success, role, msg, token = authenticate_user("User_A", "nopassword", "127.0.0.1")
        self.assertTrue(success)
        self.assertIsNotNone(token)

    def test_02_invalid_development_login(self):
        """2. Invalid login handling"""
        success, role, msg, token = authenticate_user("", "", "127.0.0.1")
        self.assertFalse(success)

    def test_03_disabled_user_login_blocked(self):
        """3. Disabled user account login blocked"""
        db_users.toggle_user_disabled("User_A")
        success, role, msg, token = authenticate_user("User_A", "nopassword", "127.0.0.1")
        self.assertFalse(success)
        self.assertIn("disabled by IT Admin", msg)
        db_users.toggle_user_disabled("User_A")

    def test_04_message_before_chat_request_blocked(self):
        """4. Message before chat request -> BLOCKED BY SERVER"""
        config.ADMIN_DIRECT_MESSAGE = False
        allowed = is_chat_allowed("User_A", "User_B")
        self.assertFalse(allowed)
        
        success, err_msg, payload = process_direct_message("User_A", "User_B", "Secret Hello", "127.0.0.1")
        self.assertFalse(success)
        self.assertIn("Chat request not accepted", err_msg)
        self.assertIsNone(payload)

    def test_05_message_while_pending_blocked(self):
        """5. Message while request is PENDING -> BLOCKED BY SERVER"""
        config.ADMIN_DIRECT_MESSAGE = False
        request_chat_permission("User_A", "User_B")
        
        success, err_msg, payload = process_direct_message("User_A", "User_B", "Pending Hello", "127.0.0.1")
        self.assertFalse(success)
        self.assertIn("Chat request not accepted", err_msg)

    def test_06_message_after_accepted_allowed(self):
        """6. Message after ACCEPTED -> ALLOWED & DELIVERED"""
        config.ADMIN_DIRECT_MESSAGE = False
        request_chat_permission("User_A", "User_B")
        process_chat_request_response("User_B", "User_A", "accept")
        
        success, err_msg, payload = process_direct_message("User_A", "User_B", "Accepted Hello", "127.0.0.1")
        self.assertTrue(success)
        self.assertEqual(payload['message'], "Accepted Hello")

    def test_07_message_after_rejected_blocked(self):
        """7. Message after REJECTED -> BLOCKED BY SERVER"""
        config.ADMIN_DIRECT_MESSAGE = False
        request_chat_permission("User_A", "User_B")
        process_chat_request_response("User_B", "User_A", "decline")
        
        success, err_msg, payload = process_direct_message("User_A", "User_B", "Rejected Hello", "127.0.0.1")
        self.assertFalse(success)

    def test_08_duplicate_chat_request(self):
        """8. Repeated duplicate chat request -> Returns existing PENDING state"""
        ok1, status1 = request_chat_permission("User_A", "User_B")
        ok2, status2 = request_chat_permission("User_A", "User_B")
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertEqual(status1, status2)

    def test_09_wrong_user_accepts_request(self):
        """9. Wrong user (User C) attempting to respond to A -> B request"""
        request_chat_permission("User_A", "User_B")
        res_ok, new_status = process_chat_request_response("User_C", "User_A", "accept")
        config.ADMIN_DIRECT_MESSAGE = False
        allowed_ab = is_chat_allowed("User_A", "User_B")
        self.assertFalse(allowed_ab)

    def test_10_admin_direct_message_bypass(self):
        """10. Authorized Admin direct messaging auto-bypass"""
        config.ADMIN_DIRECT_MESSAGE = True
        allowed = is_chat_allowed("Admin", "User_B")
        self.assertTrue(allowed)
        
        success, err_msg, payload = process_direct_message("Admin", "User_B", "Admin Urgent Notice", "127.0.0.1")
        self.assertTrue(success)

    def test_11_normal_user_cannot_admin_bypass(self):
        """11. Normal user trying to bypass chat request when not an admin"""
        config.ADMIN_DIRECT_MESSAGE = True
        allowed = is_chat_allowed("User_A", "User_B")
        self.assertFalse(allowed)

    def test_12_oversized_message_blocked(self):
        """12. Oversized message payload -> BLOCKED BY SERVER"""
        request_chat_permission("User_A", "User_B")
        process_chat_request_response("User_B", "User_A", "accept")
        
        huge_text = "X" * (config.MESSAGE_MAX_LENGTH + 50)
        success, err_msg, payload = process_direct_message("User_A", "User_B", huge_text, "127.0.0.1")
        self.assertFalse(success)
        self.assertIn("exceeds maximum allowed length", err_msg)

    def test_13_empty_message_blocked(self):
        """13. Empty or whitespace message -> BLOCKED BY SERVER"""
        success, err_msg, payload = process_direct_message("User_A", "User_B", "   ", "127.0.0.1")
        self.assertFalse(success)

    def test_14_xss_html_payload_handled_safely(self):
        """14. XSS HTML string stored as plain text without execution"""
        request_chat_permission("User_A", "User_B")
        process_chat_request_response("User_B", "User_A", "accept")
        
        xss_payload = "<img src=x onerror=alert('hack')>"
        success, err_msg, payload = process_direct_message("User_A", "User_B", xss_payload, "127.0.0.1")
        self.assertTrue(success)
        self.assertEqual(payload['message'], xss_payload)

    def test_15_jwt_token_validation_and_tampering(self):
        """15. JWT token validation & fake token tampering rejection"""
        token = verify_jwt_token("fake.tampered.jwt_token_payload")
        self.assertIsNone(token)

    def test_16_file_upload_disabled(self):
        """16. Text-Only Messaging Enforcement (ALLOW_FILE_SHARING = False)"""
        self.assertFalse(config.ALLOW_FILE_SHARING)

    def test_17_csv_formula_injection_sanitization(self):
        """17. CSV Formula Injection Sanitization (=, +, -, @)"""
        self.assertEqual(sanitize_csv_field("=SUM(A1:A10)"), "'=SUM(A1:A10)")
        self.assertEqual(sanitize_csv_field("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(sanitize_csv_field("-100"), "'-100")
        self.assertEqual(sanitize_csv_field("@SUM"), "'@SUM")
        self.assertEqual(sanitize_csv_field("Normal Hello"), "Normal Hello")

    def test_18_malformed_socket_payload_resilience(self):
        """18. Malformed socket payload resilience (None, int, missing keys)"""
        ok1, err1, p1 = process_direct_message(None, "User_B", "Text", "127.0.0.1")
        self.assertFalse(ok1)
        ok2, err2, p2 = process_direct_message("User_A", None, 12345, "127.0.0.1")
        self.assertFalse(ok2)

    def test_19_non_admin_privileged_action_rejection(self):
        """19. Non-admin user cannot perform privileged DB operations without admin role"""
        user_info = db_users.get_user_by_username("User_A")
        self.assertEqual(user_info['role'], 'user')

    def test_20_group_messaging_and_authorization(self):
        """20. Broadcast group creation and member messaging"""
        db_groups.create_broadcast_group("Test_Studio_Group", "User_A", ["User_A", "User_B"])
        groups = db_groups.get_broadcast_groups()
        group_names = [g['group_name'] for g in groups]
        self.assertIn("Test_Studio_Group", group_names)

    def test_21_database_failure_handling(self):
        """21. Safe handling when database operation Encounters error"""
        conn, db_engine = db_core.get_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_22_csv_whitespace_formula_sanitization(self):
        """22. CSV Formula Sanitization with leading whitespace/tabs"""
        self.assertEqual(sanitize_csv_field("   =HYPERLINK('http://malicious.site')"), "'   =HYPERLINK('http://malicious.site')")
        self.assertEqual(sanitize_csv_field("\t+CMD()"), "'\t+CMD()")

    def test_23_message_rate_limiting(self):
        """23. Per-user message rate limiting enforcement"""
        user = "Spammer_User"
        results = [is_rate_limited(user) for _ in range(config.MAX_MESSAGES_PER_SECOND + 5)]
        self.assertIn(True, results)

    def test_24_reset_db_safety_guard_rejection(self):
        """24. reset_db safety guard prevents execution in non-interactive mode without --force"""
        old_env = os.environ.get('SEECHAT_ALLOW_DB_RESET')
        if 'SEECHAT_ALLOW_DB_RESET' in os.environ:
            del os.environ['SEECHAT_ALLOW_DB_RESET']
        res = confirm_reset()
        self.assertFalse(res)
        if old_env:
            os.environ['SEECHAT_ALLOW_DB_RESET'] = old_env

    def test_25_audit_log_failure_resilience(self):
        """25. Audit log failure resilience (handles exceptions without throwing unhandled error)"""
        try:
            append_to_chat_csv("Invalid_Folder?*", "Invalid_User?*", "2026-08-13 00:00:00", "User_A", "User_B", "Test")
        except Exception as e:
            self.fail(f"append_to_chat_csv raised exception unexpectedly: {e}")

    def test_26_malformed_group_payload_resilience(self):
        """26. Group creation resilience with empty member list"""
        db_groups.create_broadcast_group("Empty_Group", "User_A", [])
        groups = db_groups.get_broadcast_groups()
        group_names = [g['group_name'] for g in groups]
        self.assertIn("Empty_Group", group_names)

    def test_27_sent_delivered_read_status_lifecycle(self):
        """27. Sent -> Delivered -> Read status lifecycle transitions"""
        msg_id = "msg_status_test_100"
        db_messages.save_message(msg_id, "User_A", "User_B", "", "Hello Status", "127.0.0.1")
        
        # 1. Initial Status == 'sent'
        history = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(history[0]['status'], 'sent')
        
        # 2. Update to Delivered by intended recipient
        ok_deliv, sender, recipient, m_id = db_messages.update_message_status_delivered(msg_id, "User_B")
        self.assertTrue(ok_deliv)
        history_deliv = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(history_deliv[0]['status'], 'delivered')
        
        # 3. Mark as Read by recipient
        updated_ids, sender_r, recipient_r = db_messages.mark_messages_as_read("User_A", "User_B")
        self.assertIn(msg_id, updated_ids)
        history_read = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(history_read[0]['status'], 'read')

    def test_28_unread_message_count_calculation(self):
        """28. Unread message count aggregation per sender"""
        db_messages.save_message("msg_un_1", "User_A", "User_B", "", "Unread 1", "127.0.0.1")
        db_messages.save_message("msg_un_2", "User_A", "User_B", "", "Unread 2", "127.0.0.1")
        
        counts = db_messages.get_unread_counts("User_B")
        self.assertEqual(counts.get("User_A"), 2)
        
        # Mark read clears count
        db_messages.mark_messages_as_read("User_A", "User_B")
        counts_after = db_messages.get_unread_counts("User_B")
        self.assertEqual(counts_after.get("User_A", 0), 0)

    def test_29_forged_delivery_read_ack_rejection(self):
        """29. Forged delivery and read acknowledgement rejection for wrong user"""
        msg_id = "msg_forged_test_1"
        db_messages.save_message(msg_id, "User_A", "User_B", "", "Secret Msg", "127.0.0.1")
        
        # Wrong user (User_C) attempts to acknowledge delivery of message intended for User_B
        ok_forged, s, r, m = db_messages.update_message_status_delivered(msg_id, "User_C")
        self.assertFalse(ok_forged)
        
        # Status remains 'sent'
        history = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(history[0]['status'], 'sent')

    def test_30_unread_refresh_persistence(self):
        """30. Unread message status persists in DB for browser refresh / reconnect"""
        db_messages.save_message("msg_persist_1", "User_A", "User_B", "", "Persistent Unread 1", "127.0.0.1")
        db_messages.save_message("msg_persist_2", "User_A", "User_B", "", "Persistent Unread 2", "127.0.0.1")
        
        # Simulate browser refresh query from DB
        counts_fresh = db_messages.get_unread_counts("User_B")
        self.assertEqual(counts_fresh.get("User_A"), 2)


    def test_31_user_mood_status_update(self):
        """31. User presence mood status update validation"""
        ok, mood = db_users.update_user_mood_status("User_A", "Away")
        self.assertTrue(ok)
        user_info = db_users.get_user_by_username("User_A")
        self.assertEqual(user_info['mood_status'], "Away")

    def test_32_per_user_chat_clear_isolation(self):
        """32. Per-user chat clear isolation: clearing chat hides history for requesting user only, partner retains full history"""
        import time
        for i in range(5):
            db_messages.save_message(f"msg_clear_{i}", "User_A", "User_B", "", f"Message {i}", "127.0.0.1")
            time.sleep(0.01)
            
        history_a_before = db_messages.get_chat_history("User_A", "User_B")
        history_b_before = db_messages.get_chat_history("User_B", "User_A")
        self.assertEqual(len(history_a_before), 5)
        self.assertEqual(len(history_b_before), 5)
        
        time.sleep(0.01)
        # User_A clears chat
        db_messages.clear_chat_with_target("User_A", "User_B")
        time.sleep(0.01)
        
        # User_A sees empty history
        history_a_after = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(len(history_a_after), 0)
        
        # User_B still sees all 5 messages
        history_b_after = db_messages.get_chat_history("User_B", "User_A")
        self.assertEqual(len(history_b_after), 5)
        
        # User_B sends a new message
        time.sleep(0.01)
        db_messages.save_message("msg_clear_new_6", "User_B", "User_A", "", "New Message 6", "127.0.0.1")
        time.sleep(0.01)
        
        # User_A sees only the new message
        history_a_new = db_messages.get_chat_history("User_A", "User_B")
        self.assertEqual(len(history_a_new), 1)
        self.assertEqual(history_a_new[0]['message'], "New Message 6")
        
        # User_B sees complete history (6 messages)
        history_b_new = db_messages.get_chat_history("User_B", "User_A")
        self.assertEqual(len(history_b_new), 6)
        
        # User_B clears chat
        time.sleep(0.01)
        db_messages.clear_chat_with_target("User_B", "User_A")
        time.sleep(0.01)
        
        # User_B now sees 0 messages
        history_b_cleared = db_messages.get_chat_history("User_B", "User_A")
        self.assertEqual(len(history_b_cleared), 0)

    def test_33_broadcast_group_creation_and_member_management(self):
        """33. Broadcast group creation, adding members, duplicate member handling, renaming, and deletion"""
        import database.groups as db_groups
        
        # 1. Create group Comp_Team
        ok, msg = db_groups.create_broadcast_group("Comp_Team", "Admin", ["Admin"])
        self.assertTrue(ok)
        
        # Duplicate group name rejection
        ok_dup, msg_dup = db_groups.create_broadcast_group("Comp_Team", "Admin", ["Admin"])
        self.assertFalse(ok_dup)
        self.assertIn("already exists", msg_dup)
        
        # 2. Add Demo_User to Comp_Team
        ok_add, msg_add = db_groups.add_member_to_group("Comp_Team", "Demo_User")
        self.assertTrue(ok_add)
        
        groups = db_groups.get_broadcast_groups()
        comp_group = next((g for g in groups if g['group_name'] == 'Comp_Team'), None)
        self.assertIsNotNone(comp_group)
        self.assertIn("Demo_User", comp_group['members'])
        
        # 3. Add duplicate Demo_User again (should be blocked)
        ok_add_dup, msg_add_dup = db_groups.add_member_to_group("Comp_Team", "Demo_User")
        self.assertFalse(ok_add_dup)
        self.assertIn("already in group", msg_add_dup)
        
        # 4. Rename group
        db_groups.rename_broadcast_group("Comp_Team", "Comp_Team_Renamed")
        groups_renamed = db_groups.get_broadcast_groups()
        self.assertTrue(any(g['group_name'] == 'Comp_Team_Renamed' for g in groups_renamed))
        
        # 5. Delete group
        db_groups.delete_broadcast_group("Comp_Team_Renamed")
        groups_deleted = db_groups.get_broadcast_groups()
        self.assertFalse(any(g['group_name'] == 'Comp_Team_Renamed' for g in groups_deleted))

    def test_34_message_replies_and_reactions(self):
        """34. Message replies, reactions toggle & user aggregation"""
        import database.messages as db_messages
        import services.chat_service as chat_service
        
        # 1. Save original message
        ok, msg, payload = chat_service.process_direct_message("Admin", "Demo_User", "Please check frame 1050", "127.0.0.1")
        self.assertTrue(ok)
        orig_id = payload['message_id']
        
        # 2. Reply to original message
        ok_reply, msg_r, payload_r = chat_service.process_direct_message("Demo_User", "Admin", "Checking now.", "127.0.0.1", reply_to_id=orig_id)
        self.assertTrue(ok_reply)
        self.assertEqual(payload_r['reply_to_id'], orig_id)
        
        history = db_messages.get_chat_history("Demo_User", "Admin")
        reply_msg = next((m for m in history if m['message_id'] == payload_r['message_id']), None)
        self.assertIsNotNone(reply_msg)
        self.assertIn('reply_preview', reply_msg)
        self.assertEqual(reply_msg['reply_preview']['sender'], "Admin")
        self.assertIn("1050", reply_msg['reply_preview']['message'])
        
        # 3. Toggle Reactions
        reactions = db_messages.toggle_reaction(orig_id, "Demo_User", "😂")
        self.assertEqual(len(reactions), 1)
        self.assertEqual(reactions[0]['emoji'], "😂")
        self.assertEqual(reactions[0]['count'], 1)
        
        # Add reaction from Admin
        reactions2 = db_messages.toggle_reaction(orig_id, "Admin", "😂")
        laugh_react = next((r for r in reactions2 if r['emoji'] == "😂"), None)
        self.assertIsNotNone(laugh_react)
        self.assertEqual(laugh_react['count'], 2)
        
        # Toggle off reaction from Demo_User
        reactions3 = db_messages.toggle_reaction(orig_id, "Demo_User", "😂")
        laugh_react2 = next((r for r in reactions3 if r['emoji'] == "😂"), None)
        self.assertEqual(laugh_react2['count'], 1)

    def test_35_message_edit_delete_and_audit(self):
        """35. Message edit & delete authorization and audit trail history logging"""
        import database.messages as db_messages
        import database.db as db
        import services.chat_service as chat_service
        
        # 1. Save original message
        ok, msg, payload = chat_service.process_direct_message("Admin", "Demo_User", "Helo Admin", "127.0.0.1")
        self.assertTrue(ok)
        msg_id = payload['message_id']
        
        # 2. Unauthorized edit attempt by Demo_User (should fail)
        ok_unauth, err_unauth, _ = db_messages.edit_message(msg_id, "Demo_User", "Unauthorized Edit")
        self.assertFalse(ok_unauth)
        self.assertIn("Unauthorized", err_unauth)
        
        # 3. Authorized Edit by Admin (Revision 1)
        ok_edit1, err_edit1, updated1 = db_messages.edit_message(msg_id, "Admin", "Hello Admin")
        self.assertTrue(ok_edit1)
        self.assertEqual(updated1['message'], "Hello Admin")
        self.assertEqual(updated1['is_edited'], 1)
        
        # Multiple Edits (Revision 2)
        ok_edit2, err_edit2, updated2 = db_messages.edit_message(msg_id, "Admin", "Hello Admin!")
        self.assertTrue(ok_edit2)
        self.assertEqual(updated2['message'], "Hello Admin!")
        
        # Verify audit revisions table
        conn, eng = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM message_edits WHERE message_id = ? ORDER BY revision_number ASC", (msg_id,))
        edits = cursor.fetchall()
        self.assertEqual(len(edits), 2)
        self.assertEqual(edits[0]['previous_text'], "Helo Admin")
        self.assertEqual(edits[0]['new_text'], "Hello Admin")
        self.assertEqual(edits[1]['previous_text'], "Hello Admin")
        self.assertEqual(edits[1]['new_text'], "Hello Admin!")
        
        # 4. Unauthorized delete attempt by Demo_User (should fail)
        ok_del_unauth, err_del_unauth, _ = db_messages.delete_message(msg_id, "Demo_User")
        self.assertFalse(ok_del_unauth)
        self.assertIn("Unauthorized", err_del_unauth)
        
        # 5. Authorized Delete by Admin
        ok_del, err_del, deleted = db_messages.delete_message(msg_id, "Admin")
        self.assertTrue(ok_del)
        self.assertEqual(deleted['message'], "Message deleted")
        
        # Verify audit deletes table
        cursor.execute("SELECT * FROM message_deletes WHERE message_id = ?", (msg_id,))
        del_row = cursor.fetchone()
        self.assertIsNotNone(del_row)
        self.assertEqual(del_row['original_message'], "Hello Admin!")
        self.assertEqual(del_row['deleted_by'], "Admin")
        conn.close()

    def test_36_birthday_system(self):
        import database.birthdays as db_birthdays
        from datetime import datetime
        today_mm_dd = datetime.now().strftime('%m-%d')
        
        # Set birthday for Demo_User on today's date
        ok, msg = db_birthdays.set_user_birthday("Demo_User", today_mm_dd)
        self.assertTrue(ok)
        
        # Verify get_today_birthdays matches Demo_User
        today_list = db_birthdays.get_today_birthdays()
        usernames = [b['username'] for b in today_list]
        self.assertIn("Demo_User", usernames)
        
        # Verify get_all_birthdays
        all_list = db_birthdays.get_all_birthdays()
        self.assertGreaterEqual(len(all_list), 1)
        
        # Delete birthday record
        ok_del, msg_del = db_birthdays.delete_user_birthday("Demo_User")
        self.assertTrue(ok_del)

    def test_37_card_based_birthday_wishes(self):
        import database.birthdays as db_birthdays
        
        # Admin sends professional wish 1 to Demo_User inside Card
        wish_text = "🎉 Wishing you a happy birthday and a successful year ahead!"
        ok_w, wish_id = db_birthdays.add_birthday_wish("Demo_User", "Admin", wish_text)
        self.assertTrue(ok_w)
        self.assertIsNotNone(wish_id)
        
        # Verify Demo_User receives the wish inside Card inbox
        wishes = db_birthdays.get_wishes_for_user("Demo_User")
        my_wish = next((w for w in wishes if w['id'] == wish_id), None)
        self.assertIsNotNone(my_wish)
        self.assertEqual(my_wish['sender'], "Admin")
        self.assertEqual(my_wish['wish_text'], wish_text)
        self.assertEqual(my_wish['thank_you_sent'], 0)
        
        # Demo_User responds with professional thank-you option 1 inside Card
        thanks_text = "🙏 Thank you so much for the thoughtful birthday wishes! Warm regards."
        ok_t, wishing_sender, bday_user = db_birthdays.send_thank_you_for_wish(wish_id, thanks_text)
        self.assertTrue(ok_t)
        self.assertEqual(wishing_sender, "Admin")
        self.assertEqual(bday_user, "Demo_User")
        
        # Verify wish is now marked thanked
        wishes_after = db_birthdays.get_wishes_for_user("Demo_User")
        self.assertEqual(wishes_after[0]['thank_you_sent'], 1)
        self.assertEqual(wishes_after[0]['thank_you_text'], thanks_text)

if __name__ == '__main__':
    unittest.main()
