import frappe
from frappe.model.document import Document

class FacebookMessageLog(Document):
	def before_insert(self):
		if not self.received_at and self.direction == "incoming":
			self.received_at = frappe.utils.now()
		elif not self.sent_at and self.direction == "outgoing":
			self.sent_at = frappe.utils.now()
		
		# Auto-link to existing Lead/Customer
		self.auto_link_contact()
	
	def validate(self):
		if self.message_id:
			# Check for duplicate message_id
			existing = frappe.db.exists("Facebook Message Log", {"message_id": self.message_id, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Message with ID {self.message_id} already exists")
	
	def auto_link_contact(self):
		"""Auto-link message to existing Lead or Customer"""
		if not self.sender_id or self.linked_lead:
			return
		
		# Check for existing Lead with this Facebook ID
		lead = frappe.db.get_value("Lead", {"facebook_messenger_id": self.sender_id})
		if lead:
			self.linked_lead = lead
			return
		
		# Check for existing Contact with this Facebook ID
		contact = frappe.db.get_value("Contact", {"facebook_messenger_id": self.sender_id})
		if contact:
			# Get linked Lead or Customer
			links = frappe.get_all("Dynamic Link", 
				filters={"parent": contact, "link_doctype": ["in", ["Lead", "Customer"]]},
				fields=["link_doctype", "link_name"])
			
			for link in links:
				if link.link_doctype == "Lead":
					self.linked_lead = link.link_name
					break