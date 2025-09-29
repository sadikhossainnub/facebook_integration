import frappe
from datetime import datetime, timedelta
from facebook_integration.api.insights import sync_campaign_insights
from facebook_integration.api.leads import fetch_leads as api_fetch_leads
from facebook_integration.api.shop import sync_products, sync_inventory

def sync_insights():
	"""Daily task to sync Facebook campaign insights"""
	try:
		accounts = frappe.get_all("Facebook Account", 
			filters={"enabled": 1, "enable_ads": 1},
			fields=["name"])
		
		for account in accounts:
			try:
				sync_campaign_insights(account.name)
				frappe.logger().info(f"Synced insights for account: {account.name}")
			except Exception as e:
				frappe.log_error(f"Insights sync failed for {account.name}: {str(e)}")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook insights sync task failed: {str(e)}")

def fetch_leads():
	"""Periodic task to fetch Facebook leads"""
	try:
		accounts = frappe.get_all("Facebook Account", 
			filters={"enabled": 1, "enable_leads": 1},
			fields=["name"])
		
		for account in accounts:
			try:
				result = api_fetch_leads(account.name, limit=25)
				frappe.logger().info(f"Fetched leads for {account.name}: {result}")
			except Exception as e:
				frappe.log_error(f"Lead fetch failed for {account.name}: {str(e)}")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook lead fetch task failed: {str(e)}")

def sync_shop_data():
	"""Sync Facebook Shop products and inventory"""
	try:
		accounts = frappe.get_all("Facebook Account", 
			filters={"enabled": 1, "enable_shop": 1},
			fields=["name"])
		
		for account in accounts:
			try:
				sync_products(account.name)
				sync_inventory(account.name)
				frappe.logger().info(f"Synced shop data for account: {account.name}")
			except Exception as e:
				frappe.log_error(f"Shop sync failed for {account.name}: {str(e)}")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook shop sync task failed: {str(e)}")

def cleanup_old_logs():
	"""Weekly task to cleanup old logs"""
	try:
		# Delete logs older than 90 days
		cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -90)
		
		# Cleanup message logs
		old_messages = frappe.db.get_list("Facebook Message Log",
			filters={"creation": ["<", cutoff_date]},
			pluck="name")
		
		for message_name in old_messages:
			frappe.delete_doc("Facebook Message Log", message_name, ignore_permissions=True)
		
		# Cleanup synced lead logs
		old_leads = frappe.db.get_list("Facebook Lead Log",
			filters={"creation": ["<", cutoff_date], "synced": 1},
			pluck="name")
		
		for lead_name in old_leads:
			frappe.delete_doc("Facebook Lead Log", lead_name, ignore_permissions=True)
		
		# Cleanup old campaign metrics (keep 1 year)
		old_cutoff = frappe.utils.add_days(frappe.utils.nowdate(), -365)
		old_metrics = frappe.db.get_list("Facebook Campaign Metric",
			filters={"date": ["<", old_cutoff]},
			pluck="name")
		
		for metric_name in old_metrics:
			frappe.delete_doc("Facebook Campaign Metric", metric_name, ignore_permissions=True)
		
		frappe.logger().info(f"Cleaned up {len(old_messages)} messages, {len(old_leads)} leads, {len(old_metrics)} metrics")
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Facebook logs cleanup failed: {str(e)}")