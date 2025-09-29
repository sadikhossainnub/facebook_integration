import frappe
import requests
from frappe import _
from datetime import datetime, timedelta

@frappe.whitelist()
def sync_campaign_insights(account_name, days_back=7):
	"""Sync Facebook Ads campaign insights"""
	account = frappe.get_doc("Facebook Account", account_name)
	if not account.enable_ads or not account.ad_account_id:
		return {"status": "error", "message": "Ads integration not enabled or Ad Account ID missing"}
	
	try:
		# Get campaigns
		campaigns_url = f"https://graph.facebook.com/v18.0/act_{account.ad_account_id}/campaigns"
		campaigns_params = {
			"access_token": account.get_password("access_token"),
			"fields": "id,name,status,objective",
			"limit": 100
		}
		
		campaigns_response = requests.get(campaigns_url, params=campaigns_params)
		campaigns_data = campaigns_response.json()
		
		if "error" in campaigns_data:
			return {"status": "error", "message": campaigns_data["error"]["message"]}
		
		synced_count = 0
		for campaign in campaigns_data.get("data", []):
			# Get insights for each campaign
			insights = get_campaign_insights(account, campaign["id"], days_back)
			if insights:
				save_campaign_metrics(account_name, campaign, insights)
				synced_count += 1
		
		# Update last synced
		account.last_synced = frappe.utils.now()
		account.save()
		
		return {"status": "success", "synced": synced_count}
		
	except Exception as e:
		frappe.log_error(f"Campaign insights sync error: {str(e)}")
		return {"status": "error", "message": str(e)}

def get_campaign_insights(account, campaign_id, days_back):
	"""Get insights for a specific campaign"""
	try:
		since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
		until_date = datetime.now().strftime("%Y-%m-%d")
		
		url = f"https://graph.facebook.com/v18.0/{campaign_id}/insights"
		params = {
			"access_token": account.get_password("access_token"),
			"fields": "spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,actions",
			"time_range": f"{{'since':'{since_date}','until':'{until_date}'}}",
			"time_increment": 1
		}
		
		response = requests.get(url, params=params)
		data = response.json()
		
		if "error" in data:
			frappe.log_error(f"Campaign insights API error: {data['error']['message']}")
			return None
		
		return data.get("data", [])
		
	except Exception as e:
		frappe.log_error(f"Get campaign insights error: {str(e)}")
		return None

def save_campaign_metrics(account_name, campaign, insights_data):
	"""Save campaign metrics to ERPNext"""
	try:
		for insight in insights_data:
			# Check if metric already exists
			existing = frappe.db.exists("Facebook Campaign Metric", {
				"facebook_account": account_name,
				"campaign_id": campaign["id"],
				"date": insight.get("date_start")
			})
			
			if existing:
				metric = frappe.get_doc("Facebook Campaign Metric", existing)
			else:
				metric = frappe.new_doc("Facebook Campaign Metric")
				metric.facebook_account = account_name
				metric.campaign_id = campaign["id"]
				metric.date = insight.get("date_start")
			
			# Update metrics
			metric.campaign_name = campaign.get("name", "")
			metric.campaign_status = campaign.get("status", "")
			metric.campaign_objective = campaign.get("objective", "")
			metric.spend = float(insight.get("spend", 0))
			metric.impressions = int(insight.get("impressions", 0))
			metric.clicks = int(insight.get("clicks", 0))
			metric.ctr = float(insight.get("ctr", 0))
			metric.cpc = float(insight.get("cpc", 0))
			metric.cpm = float(insight.get("cpm", 0))
			metric.reach = int(insight.get("reach", 0))
			metric.frequency = float(insight.get("frequency", 0))
			
			# Parse actions (conversions)
			actions = insight.get("actions", [])
			for action in actions:
				if action.get("action_type") == "lead":
					metric.leads = int(action.get("value", 0))
				elif action.get("action_type") == "purchase":
					metric.purchases = int(action.get("value", 0))
			
			metric.save(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(f"Save campaign metrics error: {str(e)}")

@frappe.whitelist()
def get_campaign_performance(account_name, days=30):
	"""Get campaign performance data for dashboard"""
	try:
		since_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
		
		metrics = frappe.get_all("Facebook Campaign Metric",
			filters={
				"facebook_account": account_name,
				"date": [">=", since_date]
			},
			fields=["campaign_name", "spend", "impressions", "clicks", "leads", "purchases", "date"],
			order_by="date desc"
		)
		
		# Aggregate by campaign
		campaign_data = {}
		for metric in metrics:
			campaign = metric.campaign_name
			if campaign not in campaign_data:
				campaign_data[campaign] = {
					"spend": 0,
					"impressions": 0,
					"clicks": 0,
					"leads": 0,
					"purchases": 0
				}
			
			campaign_data[campaign]["spend"] += metric.spend or 0
			campaign_data[campaign]["impressions"] += metric.impressions or 0
			campaign_data[campaign]["clicks"] += metric.clicks or 0
			campaign_data[campaign]["leads"] += metric.leads or 0
			campaign_data[campaign]["purchases"] += metric.purchases or 0
		
		# Calculate ROI and other KPIs
		for campaign in campaign_data:
			data = campaign_data[campaign]
			data["ctr"] = (data["clicks"] / data["impressions"] * 100) if data["impressions"] > 0 else 0
			data["cost_per_lead"] = (data["spend"] / data["leads"]) if data["leads"] > 0 else 0
			data["cost_per_purchase"] = (data["spend"] / data["purchases"]) if data["purchases"] > 0 else 0
		
		return {"status": "success", "data": campaign_data}
		
	except Exception as e:
		frappe.log_error(f"Get campaign performance error: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_roi_analysis(account_name, days=30):
	"""Get ROI analysis linking ad spend to sales"""
	try:
		since_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
		
		# Get ad spend
		total_spend = frappe.db.sql("""
			SELECT SUM(spend) as total_spend
			FROM `tabFacebook Campaign Metric`
			WHERE facebook_account = %s AND date >= %s
		""", (account_name, since_date), as_dict=True)[0].total_spend or 0
		
		# Get sales from Facebook leads/orders
		facebook_sales = frappe.db.sql("""
			SELECT SUM(so.grand_total) as total_sales
			FROM `tabSales Order` so
			JOIN `tabLead` l ON l.name = so.customer
			WHERE l.source = 'Facebook' AND so.creation >= %s
		""", (since_date,), as_dict=True)[0].total_sales or 0
		
		# Calculate ROI
		roi = ((facebook_sales - total_spend) / total_spend * 100) if total_spend > 0 else 0
		
		return {
			"status": "success",
			"data": {
				"total_spend": total_spend,
				"total_sales": facebook_sales,
				"roi_percentage": roi,
				"profit": facebook_sales - total_spend
			}
		}
		
	except Exception as e:
		frappe.log_error(f"ROI analysis error: {str(e)}")
		return {"status": "error", "message": str(e)}