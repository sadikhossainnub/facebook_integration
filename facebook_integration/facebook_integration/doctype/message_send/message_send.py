import frappe
from frappe.model.document import Document

class MessageSend(Document):
	def before_insert(self):
		# Auto-link to Lead
		if self.recipient_id and not self.linked_lead:
			lead = frappe.db.get_value("Lead", {"facebook_messenger_id": self.recipient_id})
			if lead:
				self.linked_lead = lead
	
	def after_insert(self):
		if self.status == "draft":
			self.send_message()
	
	def send_message(self):
		"""Send message via Facebook API"""
		try:
			from facebook_integration.api.messaging import send_message
			
			result = send_message(self.facebook_account, self.recipient_id, self.content)
			
			if result.get("success"):
				self.message_id = result.get("message_id")
				self.status = "sent"
				self.sent_at = frappe.utils.now()
				self.save()
				
				# Auto-assign future messages from this recipient to current user
				self.assign_conversation_to_user()
			else:
				self.status = "failed"
				self.save()
				frappe.throw("Failed to send message")
				
		except Exception as e:
			self.status = "failed"
			self.save()
			frappe.throw(f"Send failed: {str(e)}")
	
	def assign_conversation_to_user(self):
		"""Assign conversation to current user for fast replies"""
		# Update all unassigned messages from this recipient
		frappe.db.sql("""
			UPDATE `tabMessage Received` 
			SET assigned_to = %s
			WHERE sender_id = %s 
			AND facebook_account = %s
			AND (assigned_to IS NULL OR assigned_to = '')
		""", (self.owner, self.recipient_id, self.facebook_account))