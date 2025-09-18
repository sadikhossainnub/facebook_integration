import frappe
import requests
import json
from frappe import _

@frappe.whitelist()
def send_message(page_id, recipient_id, message):
	"""Send message via Facebook Messenger API"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		if not settings.enabled:
			frappe.throw(_("Facebook integration is not enabled"))
		
		# Prepare API request
		url = f"https://graph.facebook.com/v18.0/me/messages"
		
		headers = {
			"Content-Type": "application/json"
		}
		
		payload = {
			"recipient": {"id": recipient_id},
			"message": message,
			"access_token": settings.access_token
		}
		
		# Send request to Facebook
		response = requests.post(url, headers=headers, json=payload)
		response_data = response.json()
		
		if response.status_code == 200:
			# Log successful message
			message_log = frappe.new_doc("Facebook Message Log")
			message_log.message_id = response_data.get("message_id")
			message_log.sender_id = page_id
			message_log.recipient_id = recipient_id
			message_log.content = message.get("text", "")
			message_log.direction = "outgoing"
			message_log.status = "sent"
			message_log.sent_at = frappe.utils.now()
			
			if "text" in message:
				message_log.message_type = "text"
			elif "attachment" in message:
				message_log.message_type = message["attachment"].get("type", "file")
				message_log.media_url = message["attachment"].get("payload", {}).get("url")
			
			message_log.insert(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"message_id": response_data.get("message_id"),
				"recipient_id": response_data.get("recipient_id")
			}
		else:
			error_msg = response_data.get("error", {}).get("message", "Unknown error")
			frappe.log_error(f"Facebook API Error: {error_msg}")
			frappe.throw(_(f"Failed to send message: {error_msg}"))
			
	except Exception as e:
		frappe.log_error(f"Send message failed: {str(e)}")
		frappe.throw(_(f"Failed to send message: {str(e)}"))

@frappe.whitelist()
def get_messages(page_id=None, limit=50, after=None):
	"""Get Facebook messages for UI"""
	try:
		filters = {}
		if page_id:
			filters["recipient_id"] = page_id
		
		messages = frappe.get_list(
			"Facebook Message Log",
			filters=filters,
			fields=["*"],
			order_by="received_at desc, sent_at desc",
			limit=limit
		)
		
		return {
			"success": True,
			"messages": messages
		}
		
	except Exception as e:
		frappe.log_error(f"Get messages failed: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_conversation(sender_id, page_id):
	"""Get conversation thread between sender and page"""
	try:
		messages = frappe.get_list(
			"Facebook Message Log",
			filters={
				"sender_id": ["in", [sender_id, page_id]],
				"recipient_id": ["in", [sender_id, page_id]]
			},
			fields=["*"],
			order_by="received_at asc, sent_at asc"
		)
		
		return {
			"success": True,
			"messages": messages
		}
		
	except Exception as e:
		frappe.log_error(f"Get conversation failed: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}