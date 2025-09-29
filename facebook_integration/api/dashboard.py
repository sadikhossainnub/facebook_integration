import frappe
from frappe import _

@frappe.whitelist()
def get_dashboard_data(account_name=None, days=30):
	"""Get dashboard data for Facebook Integration"""
	try:
		filters = {}
		if account_name:
			filters["facebook_account"] = account_name
		
		since_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
		
		# Get summary stats
		stats = {
			"total_leads": get_leads_count(filters, since_date),
			"total_messages": get_messages_count(filters, since_date),
			"total_orders": get_orders_count(filters, since_date),
			"total_spend": get_ad_spend(filters, since_date),
			"conversion_rate": 0,
			"roi": 0
		}
		
		# Calculate conversion rate
		if stats["total_leads"] > 0:
			converted_leads = frappe.db.count("Facebook Lead Log", {
				**filters,
				"synced": 1,
				"creation": [">=", since_date]
			})
			stats["conversion_rate"] = (converted_leads / stats["total_leads"]) * 100
		
		# Get chart data
		charts = {
			"leads_trend": get_leads_trend(filters, days),
			"messages_trend": get_messages_trend(filters, days),
			"campaign_performance": get_campaign_performance_chart(filters, days),
			"lead_sources": get_lead_sources(filters, since_date)
		}
		
		return {
			"status": "success",
			"stats": stats,
			"charts": charts
		}
		
	except Exception as e:
		frappe.log_error(f"Dashboard data error: {str(e)}")
		return {"status": "error", "message": str(e)}

def get_leads_count(filters, since_date):
	"""Get total leads count"""
	return frappe.db.count("Facebook Lead Log", {
		**filters,
		"creation": [">=", since_date]
	})

def get_messages_count(filters, since_date):
	"""Get total messages count"""
	return frappe.db.count("Facebook Message Log", {
		**filters,
		"creation": [">=", since_date]
	})

def get_orders_count(filters, since_date):
	"""Get total orders count"""
	return frappe.db.count("Facebook Shop Order", {
		**filters,
		"creation": [">=", since_date]
	})

def get_ad_spend(filters, since_date):
	"""Get total ad spend"""
	result = frappe.db.sql("""
		SELECT SUM(spend) as total_spend
		FROM `tabFacebook Campaign Metric`
		WHERE date >= %s
		{account_filter}
	""".format(
		account_filter="AND facebook_account = %(facebook_account)s" if filters.get("facebook_account") else ""
	), {"since_date": since_date, **filters}, as_dict=True)
	
	return result[0].total_spend or 0

def get_leads_trend(filters, days):
	"""Get leads trend data"""
	data = frappe.db.sql("""
		SELECT DATE(creation) as date, COUNT(*) as count
		FROM `tabFacebook Lead Log`
		WHERE creation >= %s
		{account_filter}
		GROUP BY DATE(creation)
		ORDER BY date
	""".format(
		account_filter="AND facebook_account = %(facebook_account)s" if filters.get("facebook_account") else ""
	), {"since_date": frappe.utils.add_days(frappe.utils.nowdate(), -days), **filters}, as_dict=True)
	
	return {
		"labels": [d.date.strftime("%Y-%m-%d") for d in data],
		"datasets": [{
			"name": "Leads",
			"values": [d.count for d in data]
		}]
	}

def get_messages_trend(filters, days):
	"""Get messages trend data"""
	data = frappe.db.sql("""
		SELECT DATE(creation) as date, COUNT(*) as count
		FROM `tabFacebook Message Log`
		WHERE creation >= %s
		{account_filter}
		GROUP BY DATE(creation)
		ORDER BY date
	""".format(
		account_filter="AND facebook_account = %(facebook_account)s" if filters.get("facebook_account") else ""
	), {"since_date": frappe.utils.add_days(frappe.utils.nowdate(), -days), **filters}, as_dict=True)
	
	return {
		"labels": [d.date.strftime("%Y-%m-%d") for d in data],
		"datasets": [{
			"name": "Messages",
			"values": [d.count for d in data]
		}]
	}

def get_campaign_performance_chart(filters, days):
	"""Get campaign performance chart data"""
	data = frappe.db.sql("""
		SELECT campaign_name, SUM(spend) as spend, SUM(leads) as leads
		FROM `tabFacebook Campaign Metric`
		WHERE date >= %s
		{account_filter}
		GROUP BY campaign_name
		ORDER BY spend DESC
		LIMIT 10
	""".format(
		account_filter="AND facebook_account = %(facebook_account)s" if filters.get("facebook_account") else ""
	), {"since_date": frappe.utils.add_days(frappe.utils.nowdate(), -days), **filters}, as_dict=True)
	
	return {
		"labels": [d.campaign_name for d in data],
		"datasets": [
			{
				"name": "Spend",
				"values": [d.spend or 0 for d in data]
			},
			{
				"name": "Leads",
				"values": [d.leads or 0 for d in data]
			}
		]
	}

def get_lead_sources(filters, since_date):
	"""Get lead sources breakdown"""
	data = frappe.db.sql("""
		SELECT 
			CASE 
				WHEN synced = 1 AND lead IS NOT NULL THEN 'Converted to Lead'
				WHEN synced = 1 AND contact IS NOT NULL THEN 'Converted to Contact'
				WHEN synced = 1 AND customer IS NOT NULL THEN 'Converted to Customer'
				ELSE 'Pending'
			END as status,
			COUNT(*) as count
		FROM `tabFacebook Lead Log`
		WHERE creation >= %s
		{account_filter}
		GROUP BY status
	""".format(
		account_filter="AND facebook_account = %(facebook_account)s" if filters.get("facebook_account") else ""
	), {"since_date": since_date, **filters}, as_dict=True)
	
	return {
		"labels": [d.status for d in data],
		"datasets": [{
			"name": "Leads",
			"values": [d.count for d in data]
		}]
	}

@frappe.whitelist()
def get_account_summary():
	"""Get summary of all Facebook accounts"""
	try:
		accounts = frappe.get_all("Facebook Account",
			filters={"enabled": 1},
			fields=["name", "account_name", "page_name", "enable_leads", "enable_messenger", "enable_shop", "enable_ads"]
		)
		
		for account in accounts:
			# Get recent activity counts
			account["recent_leads"] = frappe.db.count("Facebook Lead Log", {
				"facebook_account": account.name,
				"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
			})
			
			account["recent_messages"] = frappe.db.count("Facebook Message Log", {
				"facebook_account": account.name,
				"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
			})
			
			account["recent_orders"] = frappe.db.count("Facebook Shop Order", {
				"facebook_account": account.name,
				"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
			})
		
		return {"status": "success", "accounts": accounts}
		
	except Exception as e:
		frappe.log_error(f"Account summary error: {str(e)}")
		return {"status": "error", "message": str(e)}