import frappe
import json
import hmac
import hashlib
from frappe import _

@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def webhook():
	"""Facebook webhook endpoint for verification and receiving events"""
	
	if frappe.request.method == "GET":
		return verify_webhook()
	elif frappe.request.method == "POST":
		return process_webhook()

def verify_webhook():
	"""Handle Facebook webhook verification challenge"""
	try:
		mode = frappe.form_dict.get("hub.mode")
		token = frappe.form_dict.get("hub.verify_token")
		challenge = frappe.form_dict.get("hub.challenge")
		
		settings = frappe.get_single("Facebook Settings")
		
		if mode == "subscribe" and token == settings.verify_token:
			frappe.response["type"] = "text"
			return challenge
		else:
			frappe.throw(_("Invalid verification token"), frappe.PermissionError)
			
	except Exception as e:
		frappe.log_error(f"Webhook verification failed: {str(e)}")
		frappe.throw(_("Webhook verification failed"))

def process_webhook():
	"""Process incoming Facebook webhook events"""
	try:
		# Verify signature
		if not verify_signature():
			frappe.throw(_("Invalid signature"), frappe.PermissionError)
		
		# Get request body
		body = frappe.request.get_data(as_text=True)
		data = json.loads(body)
		
		# Process each entry
		for entry in data.get("entry", []):
			process_entry(entry)
		
		return {"status": "ok"}
		
	except Exception as e:
		frappe.log_error(f"Webhook processing failed: {str(e)}")
		return {"status": "error", "message": str(e)}

def verify_signature():
	"""Verify Facebook webhook signature"""
	try:
		settings = frappe.get_single("Facebook Settings")
		signature = frappe.request.headers.get("X-Hub-Signature-256") or frappe.request.headers.get("X-Hub-Signature")
		
		if not signature:
			return False
		
		body = frappe.request.get_data()
		
		if signature.startswith("sha256="):
			expected_signature = "sha256=" + hmac.new(
				settings.app_secret.encode(),
				body,
				hashlib.sha256
			).hexdigest()
		else:
			expected_signature = "sha1=" + hmac.new(
				settings.app_secret.encode(),
				body,
				hashlib.sha1
			).hexdigest()
		
		return hmac.compare_digest(signature, expected_signature)
		
	except Exception:
		return False

def process_entry(entry):
	"""Process a single webhook entry"""
	
	# Handle messaging events
	if "messaging" in entry:
		for messaging_event in entry["messaging"]:
			process_message_event(messaging_event)
	
	# Handle leadgen events
	if "changes" in entry:
		for change in entry["changes"]:
			if change.get("field") == "leadgen":
				process_leadgen_event(change["value"])

def process_message_event(messaging_event):
	"""Process a messaging event"""
	try:
		message = messaging_event.get("message", {})
		sender = messaging_event.get("sender", {})
		recipient = messaging_event.get("recipient", {})
		
		# Create Facebook Message Log
		message_log = frappe.new_doc("Facebook Message Log")
		message_log.message_id = message.get("mid")
		message_log.sender_id = sender.get("id")
		message_log.recipient_id = recipient.get("id")
		message_log.content = message.get("text", "")
		message_log.direction = "incoming"
		message_log.status = "received"
		message_log.received_at = frappe.utils.now()
		
		# Handle different message types
		if "attachments" in message:
			attachment = message["attachments"][0]
			message_log.message_type = attachment.get("type", "file")
			message_log.media_url = attachment.get("payload", {}).get("url")
		else:
			message_log.message_type = "text"
		
		message_log.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Message processing failed: {str(e)}")

def process_leadgen_event(leadgen_data):
	"""Process a leadgen event"""
	try:
		# Create Facebook Lead Log
		lead_log = frappe.new_doc("Facebook Lead Log")
		lead_log.fb_leadgen_id = leadgen_data.get("leadgen_id")
		lead_log.page_id = leadgen_data.get("page_id")
		lead_log.form_id = leadgen_data.get("form_id")
		lead_log.data = json.dumps(leadgen_data)
		lead_log.created_at = frappe.utils.now()
		
		lead_log.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Enqueue lead processing for background
		frappe.enqueue(
			"facebook_integration.api.webhook.process_lead_data",
			lead_log_name=lead_log.name,
			queue="default"
		)
		
	except Exception as e:
		frappe.log_error(f"Leadgen processing failed: {str(e)}")

def process_lead_data(lead_log_name):
	"""Background job to process lead data and create Lead/Contact"""
	try:
		lead_log = frappe.get_doc("Facebook Lead Log", lead_log_name)
		
		# Fetch actual lead data from Facebook API
		# This would require implementing the Facebook Graph API call
		# For now, we'll mark it as processed
		lead_log.synced = 1
		lead_log.save(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Lead data processing failed: {str(e)}")