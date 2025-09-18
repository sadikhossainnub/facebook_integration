import frappe
from frappe.model.document import Document
import json

class FacebookLeadLog(Document):
	def before_insert(self):
		if not self.created_at:
			self.created_at = frappe.utils.now()
	
	def validate(self):
		if self.fb_leadgen_id:
			# Check for duplicate fb_leadgen_id
			existing = frappe.db.exists("Facebook Lead Log", {"fb_leadgen_id": self.fb_leadgen_id, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Lead with ID {self.fb_leadgen_id} already exists")
	
	def get_lead_data(self):
		"""Parse and return lead data from JSON"""
		if self.data:
			try:
				return json.loads(self.data)
			except json.JSONDecodeError:
				return {}
		return {}