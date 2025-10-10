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
			# Create Message Send record
			msg_send = frappe.new_doc("Message Send")
			msg_send.facebook_account = account_name
			msg_send.message_id = response_data.get("message_id")
			msg_send.recipient_id = recipient_id
			msg_send.content = message_text
			msg_send.status = "sent"
			msg_send.message_type = "text"
			msg_send.sent_at = frappe.utils.now()
			
			msg_send.insert(ignore_permissions=True)
			frappe.db.commit()
			
			# Create Communication record
			create_communication_record_for_sent(msg_send)
			
			# Calculate response time for previous messages
			from facebook_integration.api.assignment import calculate_response_time
			prev_messages = frappe.get_all("Message Received",
				filters={
					"sender_id": recipient_id,
					"facebook_account": account_name,
					"response_time": ["is", "not set"]
				})
			
			for msg in prev_messages:
				msg_doc = frappe.get_doc("Message Received", msg.name)
				calculate_response_time(msg_doc)
			
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
		
		# Handle message reads
		if "read" in messaging_data:
			handle_message_read(account_name, messaging_data["read"])
			return
		
		# Skip if no message content
		if not message:
			return
		
		# Create Message Received record
		msg_received = frappe.new_doc("Message Received")
		msg_received.facebook_account = account_name
		msg_received.message_id = message.get("mid")
		msg_received.sender_id = sender.get("id")
		msg_received.content = message.get("text", "")
		msg_received.status = "received"
		
		# Get sender name from Facebook API
		msg_received.sender_name = get_facebook_user_name(account_name, sender.get("id"))
		
		if "attachments" in message:
			attachment = message["attachments"][0]
			msg_received.message_type = attachment.get("type", "file")
			msg_received.media_url = attachment.get("payload", {}).get("url")
		else:
			msg_received.message_type = "text"
		
		msg_received.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Create Communication record
		create_communication_record_for_received(msg_received)
		
	except Exception as e:
		frappe.log_error(f"Message webhook handling failed: {str(e)}")

def create_communication_record_for_received(msg_received):
	"""Create ERPNext Communication record for received message"""
	try:
		# Get or create contact for sender
		contact_doc = get_or_create_contact(msg_received.sender_id, msg_received.sender_name)
		
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Facebook Messenger"
		comm.sent_or_received = "Received"
		comm.content = msg_received.content or "[Media Message]"
		comm.subject = f"Facebook Message - {msg_received.sender_name or msg_received.sender_id}"
		comm.sender = msg_received.sender_id
		comm.sender_full_name = msg_received.sender_name
		comm.reference_doctype = "Message Received"
		comm.reference_name = msg_received.name
		
		# Link to Lead or Customer if exists
		if contact_doc:
			lead = get_linked_lead(contact_doc.name)
			customer = get_linked_customer(contact_doc.name)
			
			if lead:
				comm.reference_doctype = "Lead"
				comm.reference_name = lead
			elif customer:
				comm.reference_doctype = "Customer"
				comm.reference_name = customer
		
		comm.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Communication record creation failed: {str(e)}")

def create_communication_record_for_sent(msg_send):
	"""Create ERPNext Communication record for sent message"""
	try:
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Facebook Messenger"
		comm.sent_or_received = "Sent"
		comm.content = msg_send.content
		comm.subject = f"Facebook Message to {msg_send.recipient_name or msg_send.recipient_id}"
		comm.reference_doctype = "Message Send"
		comm.reference_name = msg_send.name
		
		# Link to Lead if exists
		if msg_send.linked_lead:
			comm.reference_doctype = "Lead"
			comm.reference_name = msg_send.linked_lead
		
		comm.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Communication record creation failed: {str(e)}")

def get_or_create_contact(sender_id, sender_name=None):
	"""Get existing contact or create new Lead for Facebook sender"""
	try:
		# Check if contact exists with this Facebook ID
		contact = frappe.db.get_value("Contact", {"facebook_messenger_id": sender_id})
		if contact:
			return frappe.get_doc("Contact", contact)
		
		# Create new Lead for new Facebook contact
		lead = frappe.new_doc("Lead")
		lead.lead_name = sender_name or f"Facebook User {sender_id[:8]}"
		lead.source = "Facebook Messenger"
		lead.facebook_messenger_id = sender_id
		lead.insert(ignore_permissions=True)
		
		# Create Contact linked to Lead
		contact = frappe.new_doc("Contact")
		contact.first_name = sender_name or f"Facebook User {sender_id[:8]}"
		contact.facebook_messenger_id = sender_id
		contact.append("links", {
			"link_doctype": "Lead",
			"link_name": lead.name
		})
		contact.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return contact
		
	except Exception as e:
		frappe.log_error(f"Contact creation failed: {str(e)}")
		return None

def get_linked_lead(contact_name):
	"""Get Lead linked to contact"""
	links = frappe.get_all("Dynamic Link", 
		filters={"parent": contact_name, "link_doctype": "Lead"},
		fields=["link_name"])
	return links[0].link_name if links else None

def get_linked_customer(contact_name):
	"""Get Customer linked to contact"""
	links = frappe.get_all("Dynamic Link", 
		filters={"parent": contact_name, "link_doctype": "Customer"},
		fields=["link_name"])
	return links[0].link_name if links else None

def get_facebook_user_name(account_name, user_id):
	"""Get Facebook user name via Graph API"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		url = f"https://graph.facebook.com/v18.0/{user_id}"
		params = {
			"fields": "first_name,last_name",
			"access_token": account.get_password("access_token")
		}
		
		response = requests.get(url, params=params)
		if response.status_code == 200:
			data = response.json()
			first_name = data.get("first_name", "")
			last_name = data.get("last_name", "")
			return f"{first_name} {last_name}".strip()
		
	except Exception as e:
		frappe.log_error(f"Failed to get Facebook user name: {str(e)}")
	
	return None

def handle_message_read(account_name, read_data):
	"""Handle message read events"""
	try:
		# Update sent message status to read
		messages = frappe.get_all("Message Send",
			filters={
				"facebook_account": account_name,
				"recipient_id": read_data.get("sender", {}).get("id"),
				"status": ["in", ["sent", "delivered"]]
			})
		
		for msg in messages:
			frappe.db.set_value("Message Send", msg.name, "status", "read")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Message read handling failed: {str(e)}")

@frappe.whitelist()
def sync_messages(account_name):
	"""Sync recent messages from Facebook API"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		
		if not account.enabled or not account.enable_messenger:
			return {"success": False, "error": "Messenger not enabled"}
		
		# Get conversations from Facebook API
		url = f"https://graph.facebook.com/v18.0/{account.page_id}/conversations"
		params = {
			"fields": "participants,messages{message,from,created_time,id}",
			"access_token": account.get_password("access_token")
		}
		
		response = requests.get(url, params=params)
		if response.status_code != 200:
			return {"success": False, "error": "Failed to fetch conversations"}
		
		data = response.json()
		synced_count = 0
		
		for conversation in data.get("data", []):
			for message in conversation.get("messages", {}).get("data", []):
				if sync_single_message(account_name, message):
					synced_count += 1
		
		return {"success": True, "synced_count": synced_count}
		
	except Exception as e:
		frappe.log_error(f"Message sync failed: {str(e)}")
		return {"success": False, "error": str(e)}

def sync_single_message(account_name, message_data):
	"""Sync a single message from Facebook API"""
	try:
		message_id = message_data.get("id")
		
		# Skip if already exists
		if frappe.db.exists("Message Received", {"message_id": message_id}):
			return False
		
		account = frappe.get_doc("Facebook Account", account_name)
		from_data = message_data.get("from", {})
		
		# Create appropriate message record
		if from_data.get("id") != account.page_id:
			# Incoming message
			msg_received = frappe.new_doc("Message Received")
			msg_received.facebook_account = account_name
			msg_received.message_id = message_id
			msg_received.sender_id = from_data.get("id")
			msg_received.sender_name = from_data.get("name")
			msg_received.content = message_data.get("message", "")
			msg_received.status = "received"
			msg_received.message_type = "text"
			msg_received.received_at = message_data.get("created_time")
			msg_received.insert(ignore_permissions=True)
			create_communication_record_for_received(msg_received)
		else:
			# Outgoing message
			msg_send = frappe.new_doc("Message Send")
			msg_send.facebook_account = account_name
			msg_send.message_id = message_id
			msg_send.recipient_id = account.page_id
			msg_send.content = message_data.get("message", "")
			msg_send.status = "sent"
			msg_send.message_type = "text"
			msg_send.sent_at = message_data.get("created_time")
			msg_send.insert(ignore_permissions=True)
			create_communication_record_for_sent(msg_send)
		
		return True
		
	except Exception as e:
		frappe.log_error(f"Single message sync failed: {str(e)}")
		return False

@frappe.whitelist()
def send_reply_from_communication(communication_name, message_text):
	"""Send reply from Communication doctype"""
	try:
		comm = frappe.get_doc("Communication", communication_name)
		
		# Find Message Received reference
		if comm.reference_doctype != "Message Received":
			return {"success": False, "error": "Not a Facebook message"}
		
		msg_received = frappe.get_doc("Message Received", comm.reference_name)
		
		# Send reply
		result = send_message(msg_received.facebook_account, msg_received.sender_id, message_text)
		
		if result.get("success"):
			# Create Message Send record
			msg_send = frappe.new_doc("Message Send")
			msg_send.facebook_account = msg_received.facebook_account
			msg_send.recipient_id = msg_received.sender_id
			msg_send.recipient_name = msg_received.sender_name
			msg_send.content = message_text
			msg_send.status = "sent"
			msg_send.message_id = result.get("message_id")
			msg_send.sent_at = frappe.utils.now()
			msg_send.insert(ignore_permissions=True)
			
			# Create Communication record
			create_communication_record_for_sent(msg_send)
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Reply send failed: {str(e)}")
		return {"success": False, "error": str(e)}