import frappe
import requests
from datetime import datetime, timedelta
from frappe import _

@frappe.whitelist()
def pull_insights(since=None, until=None):
	"""Pull campaign insights from Facebook Ads API"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		if not settings.enabled:
			frappe.throw(_("Facebook integration is not enabled"))
		
		# Set default date range if not provided
		if not since:
			since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
		if not until:
			until = datetime.now().strftime("%Y-%m-%d")
		
		# Fetch campaigns first
		campaigns = fetch_campaigns()
		
		insights_data = []
		for campaign in campaigns:
			campaign_insights = fetch_campaign_insights(campaign["id"], since, until)
			insights_data.extend(campaign_insights)
		
		# Store insights in database
		for insight in insights_data:
			store_campaign_metric(insight)
		
		# Update last synced time
		settings.last_synced = frappe.utils.now()
		settings.save(ignore_permissions=True)
		frappe.db.commit()
		
		return {
			"success": True,
			"insights_count": len(insights_data),
			"date_range": f"{since} to {until}"
		}
		
	except Exception as e:
		frappe.log_error(f"Pull insights failed: {str(e)}")
		frappe.throw(_(f"Failed to pull insights: {str(e)}"))

def fetch_campaigns():
	"""Fetch campaigns from Facebook Ads API"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		url = f"https://graph.facebook.com/v18.0/act_{settings.page_id}/campaigns"
		params = {
			"access_token": settings.access_token,
			"fields": "id,name,status"
		}
		
		response = requests.get(url, params=params)
		
		if response.status_code == 200:
			return response.json().get("data", [])
		else:
			frappe.log_error(f"Facebook API Error: {response.text}")
			return []
			
	except Exception as e:
		frappe.log_error(f"Fetch campaigns failed: {str(e)}")
		return []

def fetch_campaign_insights(campaign_id, since, until):
	"""Fetch insights for a specific campaign"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		url = f"https://graph.facebook.com/v18.0/{campaign_id}/insights"
		params = {
			"access_token": settings.access_token,
			"fields": "campaign_id,campaign_name,date_start,spend,impressions,clicks,actions",
			"time_range": f"{{'since':'{since}','until':'{until}'}}",
			"time_increment": 1
		}
		
		response = requests.get(url, params=params)
		
		if response.status_code == 200:
			return response.json().get("data", [])
		else:
			frappe.log_error(f"Facebook API Error: {response.text}")
			return []
			
	except Exception as e:
		frappe.log_error(f"Fetch campaign insights failed: {str(e)}")
		return []

def store_campaign_metric(insight_data):
	"""Store campaign metric in database"""
	try:
		# Check if metric already exists
		existing = frappe.db.exists("Facebook Campaign Metric", {
			"campaign_id": insight_data.get("campaign_id"),
			"date": insight_data.get("date_start")
		})
		
		if existing:
			metric = frappe.get_doc("Facebook Campaign Metric", existing)
		else:
			metric = frappe.new_doc("Facebook Campaign Metric")
			metric.campaign_id = insight_data.get("campaign_id")
			metric.date = insight_data.get("date_start")
		
		metric.campaign_name = insight_data.get("campaign_name")
		metric.spend = float(insight_data.get("spend", 0))
		metric.impressions = int(insight_data.get("impressions", 0))
		metric.clicks = int(insight_data.get("clicks", 0))
		
		# Extract leads and conversions from actions
		actions = insight_data.get("actions", [])
		metric.leads = sum(int(action["value"]) for action in actions if action["action_type"] == "lead")
		metric.conversions = sum(int(action["value"]) for action in actions if action["action_type"] in ["purchase", "complete_registration"])
		
		# Calculate ROAS (Return on Ad Spend)
		if metric.spend > 0 and metric.conversions > 0:
			# This is a simplified ROAS calculation - you might want to use actual revenue data
			metric.roas = metric.conversions / metric.spend
		
		if existing:
			metric.save(ignore_permissions=True)
		else:
			metric.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Store campaign metric failed: {str(e)}")

@frappe.whitelist()
def get_campaign_metrics(campaign_id=None, from_date=None, to_date=None):
	"""Get campaign metrics for reporting"""
	try:
		filters = {}
		if campaign_id:
			filters["campaign_id"] = campaign_id
		if from_date:
			filters["date"] = [">=", from_date]
		if to_date:
			if "date" in filters:
				filters["date"] = ["between", [from_date, to_date]]
			else:
				filters["date"] = ["<=", to_date]
		
		metrics = frappe.get_list(
			"Facebook Campaign Metric",
			filters=filters,
			fields=["*"],
			order_by="date desc"
		)
		
		return {
			"success": True,
			"metrics": metrics
		}
		
	except Exception as e:
		frappe.log_error(f"Get campaign metrics failed: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def refresh_token():
	"""Refresh Facebook access token"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		# This is a simplified token refresh - in practice, you'd need to implement
		# the full OAuth flow or use a long-lived token exchange
		url = "https://graph.facebook.com/v18.0/oauth/access_token"
		params = {
			"grant_type": "fb_exchange_token",
			"client_id": settings.app_id,
			"client_secret": settings.app_secret,
			"fb_exchange_token": settings.access_token
		}
		
		response = requests.get(url, params=params)
		
		if response.status_code == 200:
			data = response.json()
			settings.access_token = data.get("access_token")
			settings.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"message": "Token refreshed successfully"
			}
		else:
			frappe.log_error(f"Token refresh failed: {response.text}")
			return {
				"success": False,
				"error": "Failed to refresh token"
			}
			
	except Exception as e:
		frappe.log_error(f"Refresh token failed: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}