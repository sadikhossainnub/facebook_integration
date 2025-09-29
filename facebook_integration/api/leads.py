import frappe
import json
import requests
from frappe import _

@frappe.whitelist()
def fetch_leads(account_name, limit=50):
	"""Fetch leads from Facebook Lead Ads"""
	account = frappe.get_doc("Facebook Account", account_name)
	if not account.enable_leads:
		return {"status": "error", "message": "Lead Ads not enabled"}
	
	try:
		url = f"https://graph.facebook.com/v18.0/{account.page_id}/leadgen_forms"
		params = {
			"access_token": account.get_password("access_token"),
			"fields": "id,name,leads{id,created_time,field_data}",
			"limit": limit
		}
		
		response = requests.get(url, params=params)
		data = response.json()
		
		if "error" in data:
			return {"status": "error", "message": data["error"]["message"]}
		
		processed_count = 0
		for form in data.get("data", []):
			for lead in form.get("leads", {}).get("data", []):
				process_facebook_lead(account_name, lead)
				processed_count += 1
		
		return {"status": "success", "processed": processed_count}
		
	except Exception as e:
		frappe.log_error(f"Lead fetch error: {str(e)}")
		return {"status": "error", "message": str(e)}

@frappe.whitelist()
def map_lead(lead_log_name, doctype="Lead"):
	"""Map Facebook lead to ERPNext Lead/Contact/Customer"""
	lead_log = frappe.get_doc("Facebook Lead Log", lead_log_name)
	
	if doctype == "Lead":
		return create_erp_lead(lead_log)
	elif doctype == "Contact":
		return create_erp_contact(lead_log)
	elif doctype == "Customer":
		return create_erp_customer(lead_log)

def process_facebook_lead(account_name, lead_data):
	"""Process single Facebook lead"""
	fb_lead_id = lead_data.get("id")
	
	# Check if already processed
	if frappe.db.exists("Facebook Lead Log", {"fb_leadgen_id": fb_lead_id}):
		return
	
	# Create lead log
	lead_log = frappe.new_doc("Facebook Lead Log")
	lead_log.facebook_account = account_name
	lead_log.fb_leadgen_id = fb_lead_id
	lead_log.created_at = lead_data.get("created_time")
	lead_log.data = frappe.as_json(lead_data)
	
	# Parse field data
	field_data = {}
	for field in lead_data.get("field_data", []):
		field_data[field.get("name")] = field.get("values", [None])[0]
	
	lead_log.email = field_data.get("email")
	lead_log.phone = field_data.get("phone_number")
	lead_log.full_name = field_data.get("full_name")
	lead_log.company_name = field_data.get("company_name")
	
	lead_log.insert(ignore_permissions=True)
	
	# Auto-create ERPNext Lead if enabled
	account = frappe.get_doc("Facebook Account", account_name)
	if account.default_lead_owner:
		create_erp_lead(lead_log)

def create_erp_lead(lead_log):
	"""Create ERPNext Lead from Facebook Lead"""
	try:
		lead = frappe.new_doc("Lead")
		lead.lead_name = lead_log.full_name or "Facebook Lead"
		lead.email_id = lead_log.email
		lead.mobile_no = lead_log.phone
		lead.company_name = lead_log.company_name
		lead.source = "Facebook"
		lead.lead_owner = frappe.db.get_value("Facebook Account", lead_log.facebook_account, "default_lead_owner")
		
		lead.insert()
		
		lead_log.lead = lead.name
		lead_log.synced = 1
		lead_log.save()
		
		return {"status": "success", "lead": lead.name}
	except Exception as e:
		frappe.log_error(f"Lead creation failed: {str(e)}")
		return {"status": "error", "message": str(e)}

def create_erp_contact(lead_log):
	"""Create ERPNext Contact from Facebook Lead"""
	try:
		contact = frappe.new_doc("Contact")
		contact.first_name = lead_log.full_name or "Facebook Contact"
		contact.email_id = lead_log.email
		contact.mobile_no = lead_log.phone
		
		contact.insert()
		
		lead_log.contact = contact.name
		lead_log.synced = 1
		lead_log.save()
		
		return {"status": "success", "contact": contact.name}
	except Exception as e:
		frappe.log_error(f"Contact creation failed: {str(e)}")
		return {"status": "error", "message": str(e)}

def create_erp_customer(lead_log):
	"""Create ERPNext Customer from Facebook Lead"""
	try:
		customer = frappe.new_doc("Customer")
		customer.customer_name = lead_log.full_name or "Facebook Customer"
		customer.customer_type = "Individual"
		customer.email_id = lead_log.email
		customer.mobile_no = lead_log.phone
		
		customer.insert()
		
		lead_log.customer = customer.name
		lead_log.synced = 1
		lead_log.save()
		
		return {"status": "success", "customer": customer.name}
	except Exception as e:
		frappe.log_error(f"Customer creation failed: {str(e)}")
		return {"status": "error", "message": str(e)}

def handle_lead_webhook(account_name, leadgen_data):
	"""Handle lead webhook from Facebook"""
	try:
		lead_id = leadgen_data.get("leadgen_id")
		
		# Fetch full lead data from Facebook API
		account = frappe.get_doc("Facebook Account", account_name)
		url = f"https://graph.facebook.com/v18.0/{lead_id}"
		params = {
			"access_token": account.get_password("access_token"),
			"fields": "id,created_time,field_data"
		}
		
		response = requests.get(url, params=params)
		lead_data = response.json()
		
		if "error" not in lead_data:
			process_facebook_lead(account_name, lead_data)
		
	except Exception as e:
		frappe.log_error(f"Lead webhook handling failed: {str(e)}")

@frappe.whitelist()
def get_unmapped_leads(account_name=None, limit=50):
	"""Get unmapped Facebook leads"""
	try:
		filters = {"synced": 0}
		if account_name:
			filters["facebook_account"] = account_name
			
		leads = frappe.get_list(
			"Facebook Lead Log",
			filters=filters,
			fields=["*"],
			order_by="created_at desc",
			limit=limit
		)
		
		return {
			"success": True,
			"leads": leads
		}
		
	except Exception as e:
		frappe.log_error(f"Get unmapped leads failed: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}