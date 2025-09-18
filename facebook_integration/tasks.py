import frappe
from datetime import datetime, timedelta
from facebook_integration.api.insights import pull_insights
from facebook_integration.api.leads import fetch_lead_from_facebook

def sync_insights():
	"""Daily task to sync Facebook insights"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		if not settings.enabled:
			return
		
		# Pull insights for yesterday
		yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
		
		frappe.logger().info(f"Starting Facebook insights sync for {yesterday}")
		
		result = pull_insights(since=yesterday, until=yesterday)
		
		frappe.logger().info(f"Facebook insights sync completed: {result}")
		
	except Exception as e:
		frappe.log_error(f"Facebook insights sync failed: {str(e)}")

def fetch_leads():
	"""Periodic task to fetch pending leads"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		if not settings.enabled:
			return
		
		# Get unprocessed leads
		pending_leads = frappe.get_list(
			"Facebook Lead Log",
			filters={"synced": 0},
			fields=["name", "fb_leadgen_id"],
			limit=10
		)
		
		for lead in pending_leads:
			try:
				# Fetch lead data from Facebook
				lead_data = fetch_lead_from_facebook(lead["fb_leadgen_id"])
				
				if lead_data:
					# Update lead log with fetched data
					lead_doc = frappe.get_doc("Facebook Lead Log", lead["name"])
					lead_doc.data = frappe.as_json(lead_data)
					lead_doc.save(ignore_permissions=True)
					
					frappe.logger().info(f"Updated lead data for {lead['fb_leadgen_id']}")
				
			except Exception as e:
				frappe.log_error(f"Failed to fetch lead {lead['fb_leadgen_id']}: {str(e)}")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook leads fetch failed: {str(e)}")

def cleanup_old_logs():
	"""Weekly task to cleanup old logs"""
	try:
		# Delete message logs older than 90 days
		cutoff_date = datetime.now() - timedelta(days=90)
		
		old_messages = frappe.get_list(
			"Facebook Message Log",
			filters={"creation": ["<", cutoff_date]},
			pluck="name"
		)
		
		for message_name in old_messages:
			frappe.delete_doc("Facebook Message Log", message_name, ignore_permissions=True)
		
		frappe.logger().info(f"Cleaned up {len(old_messages)} old Facebook message logs")
		
		# Delete campaign metrics older than 1 year
		old_cutoff = datetime.now() - timedelta(days=365)
		
		old_metrics = frappe.get_list(
			"Facebook Campaign Metric",
			filters={"date": ["<", old_cutoff.strftime("%Y-%m-%d")]},
			pluck="name"
		)
		
		for metric_name in old_metrics:
			frappe.delete_doc("Facebook Campaign Metric", metric_name, ignore_permissions=True)
		
		frappe.logger().info(f"Cleaned up {len(old_metrics)} old Facebook campaign metrics")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook logs cleanup failed: {str(e)}")