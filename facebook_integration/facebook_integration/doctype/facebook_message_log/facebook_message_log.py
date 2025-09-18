import frappe
from frappe.model.document import Document

class FacebookMessageLog(Document):
	def before_insert(self):
		if not self.received_at and self.direction == "incoming":
			self.received_at = frappe.utils.now()
		elif not self.sent_at and self.direction == "outgoing":
			self.sent_at = frappe.utils.now()
	
	def validate(self):
		if self.message_id:
			# Check for duplicate message_id
			existing = frappe.db.exists("Facebook Message Log", {"message_id": self.message_id, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Message with ID {self.message_id} already exists")