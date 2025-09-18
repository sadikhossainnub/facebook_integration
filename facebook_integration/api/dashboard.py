import frappe
from frappe.utils import today, get_datetime

@frappe.whitelist()
def get_facebook_stats():
	"""Get Facebook integration statistics"""
	stats = {
		'total_messages': 0,
		'total_leads': 0,
		'unmapped_leads': 0,
		'today_messages': 0
	}
	
	try:
		# Total messages
		stats['total_messages'] = frappe.db.count('Facebook Message Log')
		
		# Total leads
		stats['total_leads'] = frappe.db.count('Facebook Lead Log')
		
		# Unmapped leads
		stats['unmapped_leads'] = frappe.db.count('Facebook Lead Log', {'synced': 0})
		
		# Today's messages
		today_start = get_datetime(today())
		stats['today_messages'] = frappe.db.count('Facebook Message Log', {
			'creation': ['>=', today_start]
		})
		
	except Exception as e:
		frappe.log_error(f"Error getting Facebook stats: {str(e)}")
	
	return stats

@frappe.whitelist()
def test_connection():
	"""Test Facebook API connection"""
	try:
		settings = frappe.get_single("Facebook Settings")
		if not settings.enabled:
			return {"success": False, "message": "Facebook integration is disabled"}
		
		if not settings.access_token:
			return {"success": False, "message": "Access token not configured"}
		
		# Simple API test - get page info
		import requests
		url = f"https://graph.facebook.com/v18.0/{settings.page_id}"
		params = {
			'access_token': settings.access_token,
			'fields': 'name,id'
		}
		
		response = requests.get(url, params=params)
		if response.status_code == 200:
			data = response.json()
			return {
				"success": True, 
				"message": f"Connected to page: {data.get('name', 'Unknown')}"
			}
		else:
			return {
				"success": False, 
				"message": f"API Error: {response.status_code}"
			}
			
	except Exception as e:
		frappe.log_error(f"Facebook connection test failed: {str(e)}")
		return {"success": False, "message": str(e)}

@frappe.whitelist()
def auto_map_leads():
	"""Auto map Facebook leads to ERPNext leads"""
	try:
		unmapped_leads = frappe.get_list(
			"Facebook Lead Log",
			filters={"synced": 0},
			fields=["name", "fb_leadgen_id", "lead_data"]
		)
		
		mapped_count = 0
		for lead_log in unmapped_leads:
			try:
				# Parse lead data
				import json
				lead_data = json.loads(lead_log.lead_data or '{}')
				
				# Extract basic info
				email = None
				phone = None
				full_name = None
				
				for field in lead_data.get('field_data', []):
					if field.get('name') == 'email':
						email = field.get('values', [{}])[0].get('value')
					elif field.get('name') == 'phone_number':
						phone = field.get('values', [{}])[0].get('value')
					elif field.get('name') == 'full_name':
						full_name = field.get('values', [{}])[0].get('value')
				
				if email or phone:
					# Create ERPNext Lead
					lead_doc = frappe.new_doc("Lead")
					lead_doc.lead_name = full_name or "Facebook Lead"
					if email:
						lead_doc.email_id = email
					if phone:
						lead_doc.phone = phone
					lead_doc.source = "Facebook"
					lead_doc.save()
					
					# Update Facebook Lead Log
					frappe.db.set_value("Facebook Lead Log", lead_log.name, {
						"synced": 1,
						"erpnext_lead": lead_doc.name
					})
					
					mapped_count += 1
					
			except Exception as e:
				frappe.log_error(f"Error mapping lead {lead_log.name}: {str(e)}")
				continue
		
		frappe.db.commit()
		return {"success": True, "mapped_count": mapped_count}
		
	except Exception as e:
		frappe.log_error(f"Auto mapping failed: {str(e)}")
		return {"success": False, "message": str(e)}