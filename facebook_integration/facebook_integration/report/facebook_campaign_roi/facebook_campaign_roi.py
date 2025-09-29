import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Campaign"),
			"fieldname": "campaign_name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Spend"),
			"fieldname": "total_spend",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Impressions"),
			"fieldname": "total_impressions",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("Clicks"),
			"fieldname": "total_clicks",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Leads"),
			"fieldname": "total_leads",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("CTR %"),
			"fieldname": "ctr",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"label": _("Cost per Lead"),
			"fieldname": "cost_per_lead",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Revenue"),
			"fieldname": "revenue",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("ROI %"),
			"fieldname": "roi",
			"fieldtype": "Percent",
			"width": 100
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	# Get campaign metrics
	campaign_data = frappe.db.sql(f"""
		SELECT 
			campaign_name,
			SUM(spend) as total_spend,
			SUM(impressions) as total_impressions,
			SUM(clicks) as total_clicks,
			SUM(leads) as total_leads
		FROM `tabFacebook Campaign Metric`
		{conditions}
		GROUP BY campaign_name
		ORDER BY total_spend DESC
	""", filters, as_dict=1)
	
	# Calculate derived metrics
	for row in campaign_data:
		# CTR
		row['ctr'] = (row['total_clicks'] / row['total_impressions'] * 100) if row['total_impressions'] > 0 else 0
		
		# Cost per lead
		row['cost_per_lead'] = (row['total_spend'] / row['total_leads']) if row['total_leads'] > 0 else 0
		
		# Get revenue from sales orders linked to Facebook leads
		revenue = get_campaign_revenue(row['campaign_name'], filters)
		row['revenue'] = revenue
		
		# ROI
		row['roi'] = ((revenue - row['total_spend']) / row['total_spend'] * 100) if row['total_spend'] > 0 else 0
	
	return campaign_data

def get_campaign_revenue(campaign_name, filters):
	"""Get revenue generated from a specific campaign"""
	# This is a simplified approach - in reality you'd need better campaign-to-sale tracking
	conditions = get_conditions(filters, table_prefix="fcm.")
	
	revenue = frappe.db.sql(f"""
		SELECT COALESCE(SUM(so.grand_total), 0) as revenue
		FROM `tabFacebook Campaign Metric` fcm
		JOIN `tabFacebook Lead Log` fll ON fcm.facebook_account = fll.facebook_account
		JOIN `tabLead` l ON fll.lead = l.name
		JOIN `tabSales Order` so ON l.name = so.customer
		WHERE fcm.campaign_name = %s
		{conditions}
	""", (campaign_name,), as_dict=1)
	
	return revenue[0]['revenue'] if revenue else 0

def get_conditions(filters, table_prefix=""):
	conditions = "WHERE 1=1"
	
	if filters.get("from_date"):
		conditions += f" AND DATE({table_prefix}date) >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += f" AND DATE({table_prefix}date) <= %(to_date)s"
	
	if filters.get("facebook_account"):
		conditions += f" AND {table_prefix}facebook_account = %(facebook_account)s"
	
	return conditions