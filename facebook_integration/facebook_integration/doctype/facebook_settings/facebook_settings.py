import frappe
from frappe.model.document import Document

class FacebookSettings(Document):
	def validate(self):
		if self.enabled and not all([self.page_id, self.app_id, self.app_secret, self.access_token, self.verify_token]):
			frappe.throw("All required fields must be filled to enable Facebook integration")
		
		# Set webhook URL
		if not self.webhook_url:
			site_url = frappe.utils.get_url()
			self.webhook_url = f"{site_url}/api/method/facebook_integration.api.webhook"