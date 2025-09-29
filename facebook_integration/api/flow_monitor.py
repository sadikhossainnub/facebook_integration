import frappe
from frappe import _

@frappe.whitelist()
def get_flow_status():
	"""Get real-time status of Facebook integration flows"""
	try:
		status = {
			"webhook_status": check_webhook_status(),
			"sync_status": check_sync_status(),
			"recent_activity": get_recent_activity(),
			"error_summary": get_error_summary()
		}
		return {"status": "success", "data": status}
	except Exception as e:
		frappe.log_error(f"Flow status error: {str(e)}")
		return {"status": "error", "message": str(e)}

def check_webhook_status():
	"""Check webhook connectivity status"""
	accounts = frappe.get_all("Facebook Account", 
		filters={"enabled": 1}, 
		fields=["name", "account_name", "last_synced"])
	
	for account in accounts:
		# Check recent webhook activity
		recent_messages = frappe.db.count("Facebook Message Log", {
			"facebook_account": account.name,
			"creation": [">=", frappe.utils.add_hours(frappe.utils.now(), -1)]
		})
		
		recent_leads = frappe.db.count("Facebook Lead Log", {
			"facebook_account": account.name,
			"creation": [">=", frappe.utils.add_hours(frappe.utils.now(), -1)]
		})
		
		account["webhook_active"] = recent_messages > 0 or recent_leads > 0
	
	return accounts

def check_sync_status():
	"""Check scheduled sync status"""
	return {
		"last_insights_sync": frappe.db.get_value("Facebook Campaign Metric", 
			None, "MAX(modified)"),
		"pending_leads": frappe.db.count("Facebook Lead Log", {"synced": 0}),
		"pending_orders": frappe.db.count("Facebook Shop Order", {"status": "Pending"})
	}

def get_recent_activity():
	"""Get recent activity across all flows"""
	return {
		"leads_today": frappe.db.count("Facebook Lead Log", {
			"creation": [">=", frappe.utils.nowdate()]
		}),
		"messages_today": frappe.db.count("Facebook Message Log", {
			"creation": [">=", frappe.utils.nowdate()]
		}),
		"orders_today": frappe.db.count("Facebook Shop Order", {
			"creation": [">=", frappe.utils.nowdate()]
		})
	}

def get_error_summary():
	"""Get recent error summary"""
	errors = frappe.get_all("Error Log",
		filters={
			"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -1)],
			"error": ["like", "%facebook%"]
		},
		fields=["error", "creation"],
		limit=5,
		order_by="creation desc"
	)
	
	return len(errors)