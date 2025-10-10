import frappe
from frappe.model.document import Document

class MessageReceived(Document):
	def before_insert(self):
		if not self.received_at:
			self.received_at = frappe.utils.now()
		
		# Auto-link to Lead
		if self.sender_id and not self.linked_lead:
			lead = frappe.db.get_value("Lead", {"facebook_messenger_id": self.sender_id})
			if lead:
				self.linked_lead = lead
		
		# Auto-assign conversation
		self.auto_assign_conversation()
	
	def validate(self):
		if self.message_id:
			existing = frappe.db.exists("Message Received", {"message_id": self.message_id, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Message with ID {self.message_id} already exists")
	
	def auto_assign_conversation(self):
		"""Auto-assign conversation to user who replied fastest"""
		# Check if conversation already assigned
		last_msg = frappe.db.get_value("Message Received", 
			{"sender_id": self.sender_id, "facebook_account": self.facebook_account, "assigned_to": ["is", "set"]}, 
			["assigned_to"], order_by="received_at desc")
		
		if last_msg:
			self.assigned_to = last_msg
			return
		
		# Check for recent reply from any user
		recent_reply = frappe.db.sql("""
			SELECT ms.owner 
			FROM `tabMessage Send` ms
			WHERE ms.recipient_id = %s 
			AND ms.facebook_account = %s
			AND ms.sent_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
			ORDER BY ms.sent_at DESC
			LIMIT 1
		""", (self.sender_id, self.facebook_account))
		
		if recent_reply:
			self.assigned_to = recent_reply[0][0]