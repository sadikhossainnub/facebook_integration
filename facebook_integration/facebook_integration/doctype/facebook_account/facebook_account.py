import frappe
from frappe.model.document import Document

class FacebookAccount(Document):
	def validate(self):
		if not self.webhook_url:
			self.webhook_url = f"{frappe.utils.get_url()}/api/method/facebook_integration.api.webhook.handle_webhook"
	
	def on_update(self):
		if self.enabled:
			frappe.enqueue("facebook_integration.api.webhook.setup_webhook", account=self.name)