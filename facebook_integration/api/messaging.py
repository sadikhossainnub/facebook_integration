import frappe
import requests
import json
from frappe import _

@frappe.whitelist()
def send_message(account_name, recipient_id, message_text):
	"""Send message via Facebook Messenger API"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		
		if not account.enabled or not account.enable_messenger:
			frappe.throw(_("Messenger integration is not enabled"))
		
		# Prepare API request
		url = f"https://graph.facebook.com/v18.0/me/messages"
		
		headers = {
			"Content-Type": "application/json"
		}
		
		payload = {
			"recipient": {"id": recipient_id},
			"message": {"text": message_text},
			"access_token": account.get_password("access_token")
		}
		
		# Send request to Facebook
		response = requests.post(url, headers=headers, json=payload)
		response_data = response.json()
		
		if response.status_code == 200:
			# Log successful message
			message_log = frappe.new_doc("Facebook Message Log")
			message_log.facebook_account = account_name
			message_log.message_id = response_data.get("message_id")
			message_log.sender_id = account.page_id
			message_log.recipient_id = recipient_id
			message_log.content = message_text
			message_log.direction = "outgoing"
			message_log.status = "sent"
			message_log.message_type = "text"
			message_log.sent_at = frappe.utils.now()
			
			message_log.insert(ignore_permissions=True)
			frappe.db.commit()
			
			# Create Communication record
			create_communication_record(message_log)
			
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
def get_messages(account_name=None, limit=50):
	"""Get Facebook messages for UI"""
	try:
		filters = {}
		if account_name:
			filters["facebook_account"] = account_name
			
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
def get_conversation(sender_id, account_name):
	"""Get conversation thread between sender and page"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		
		messages = frappe.get_list(
			"Facebook Message Log",
			filters={
				"facebook_account": account_name,
				"sender_id": ["in", [sender_id, account.page_id]],
				"recipient_id": ["in", [sender_id, account.page_id]]
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

def handle_message_webhook(account_name, messaging_data):
	"""Handle incoming message from webhook"""
	try:
		message = messaging_data.get("message", {})
		sender = messaging_data.get("sender", {})
		
		msg_log = frappe.new_doc("Facebook Message Log")
		msg_log.facebook_account = account_name
		msg_log.message_id = message.get("mid")
		msg_log.sender_id = sender.get("id")
		msg_log.content = message.get("text", "")
		msg_log.direction = "incoming"
		msg_log.status = "received"
		msg_log.received_at = frappe.utils.now()
		
		if "attachments" in message:
			attachment = message["attachments"][0]
			msg_log.message_type = attachment.get("type", "file")
			msg_log.media_url = attachment.get("payload", {}).get("url")
		else:
			msg_log.message_type = "text"
		
		msg_log.insert(ignore_permissions=True)
		
		# Create Communication record
		create_communication_record(msg_log)
		
	except Exception as e:
		frappe.log_error(f"Message webhook handling failed: {str(e)}")

def create_communication_record(msg_log):
	"""Create ERPNext Communication record"""
	try:
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Social Media"
		comm.sent_or_received = "Received" if msg_log.direction == "incoming" else "Sent"
		comm.content = msg_log.content
		comm.subject = f"Facebook Message from {msg_log.sender_id}"
		comm.sender = msg_log.sender_id
		comm.reference_doctype = "Facebook Message Log"
		comm.reference_name = msg_log.name
		comm.insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Communication record creation failed: {str(e)}")