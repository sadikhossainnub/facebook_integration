import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def get_my_conversations():
	"""Get conversations assigned to current user"""
	conversations = frappe.db.sql("""
		SELECT DISTINCT sender_id, sender_name, facebook_account,
			MAX(received_at) as last_message_time,
			COUNT(*) as message_count
		FROM `tabMessage Received`
		WHERE assigned_to = %s
		GROUP BY sender_id, facebook_account
		ORDER BY last_message_time DESC
	""", frappe.session.user, as_dict=True)
	
	return conversations

@frappe.whitelist()
def assign_conversation(sender_id, facebook_account, user=None):
	"""Manually assign conversation to user"""
	if not user:
		user = frappe.session.user
	
	frappe.db.sql("""
		UPDATE `tabMessage Received` 
		SET assigned_to = %s
		WHERE sender_id = %s 
		AND facebook_account = %s
	""", (user, sender_id, facebook_account))
	
	frappe.db.commit()
	return {"success": True}

@frappe.whitelist()
def get_response_stats():
	"""Get response time statistics for current user"""
	stats = frappe.db.sql("""
		SELECT 
			AVG(response_time) as avg_response_time,
			MIN(response_time) as fastest_response,
			COUNT(*) as total_responses
		FROM `tabMessage Received`
		WHERE assigned_to = %s
		AND response_time IS NOT NULL
		AND response_time > 0
	""", frappe.session.user, as_dict=True)
	
	return stats[0] if stats else {}

def calculate_response_time(msg_received):
	"""Calculate response time for a message"""
	if not msg_received.assigned_to:
		return
	
	# Find the next outgoing message from assigned user
	next_reply = frappe.db.sql("""
		SELECT sent_at
		FROM `tabMessage Send`
		WHERE recipient_id = %s
		AND facebook_account = %s
		AND owner = %s
		AND sent_at > %s
		ORDER BY sent_at ASC
		LIMIT 1
	""", (msg_received.sender_id, msg_received.facebook_account, 
		  msg_received.assigned_to, msg_received.received_at))
	
	if next_reply:
		response_time = (next_reply[0][0] - msg_received.received_at).total_seconds()
		frappe.db.set_value("Message Received", msg_received.name, "response_time", int(response_time))