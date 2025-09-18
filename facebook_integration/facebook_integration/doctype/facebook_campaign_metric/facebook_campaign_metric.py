import frappe
from frappe.model.document import Document

class FacebookCampaignMetric(Document):
	def validate(self):
		# Ensure unique combination of campaign_id and date
		if self.campaign_id and self.date:
			existing = frappe.db.exists("Facebook Campaign Metric", {
				"campaign_id": self.campaign_id,
				"date": self.date,
				"name": ["!=", self.name]
			})
			if existing:
				frappe.throw(f"Metric for campaign {self.campaign_id} on {self.date} already exists")