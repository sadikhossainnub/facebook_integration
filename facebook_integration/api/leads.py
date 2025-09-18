import frappe
import json
import requests
from frappe import _

@frappe.whitelist()
def map_lead(fb_lead_id, map_to, field_map):
	"""Map Facebook lead to ERPNext Lead/Contact/Customer"""
	try:
		# Get Facebook Lead Log
		lead_log = frappe.get_doc("Facebook Lead Log", {"fb_leadgen_id": fb_lead_id})
		
		if not lead_log:
			frappe.throw(_("Facebook lead not found"))
		
		# Parse lead data
		lead_data = json.loads(lead_log.data) if lead_log.data else {}
		
		# Fetch actual lead data from Facebook API if needed
		if not lead_data.get("field_data"):
			lead_data = fetch_lead_from_facebook(fb_lead_id)
		
		# Create ERPNext document based on mapping
		if map_to == "Lead":
			doc = create_lead(lead_data, field_map)
		elif map_to == "Contact":
			doc = create_contact(lead_data, field_map)
		elif map_to == "Customer":
			doc = create_customer(lead_data, field_map)
		else:
			frappe.throw(_("Invalid mapping target"))
		
		# Update lead log
		lead_log.mapped_to = map_to
		lead_log.mapped_document = doc.name
		lead_log.synced = 1
		lead_log.save(ignore_permissions=True)
		frappe.db.commit()
		
		return {
			"success": True,
			"document_type": map_to,
			"document_name": doc.name
		}
		
	except Exception as e:
		frappe.log_error(f"Lead mapping failed: {str(e)}")
		frappe.throw(_(f"Failed to map lead: {str(e)}"))

def fetch_lead_from_facebook(leadgen_id):
	"""Fetch lead data from Facebook Graph API"""
	try:
		settings = frappe.get_single("Facebook Settings")
		
		url = f"https://graph.facebook.com/v18.0/{leadgen_id}"
		params = {
			"access_token": settings.access_token
		}
		
		response = requests.get(url, params=params)
		
		if response.status_code == 200:
			return response.json()
		else:
			frappe.log_error(f"Facebook API Error: {response.text}")
			return {}
			
	except Exception as e:
		frappe.log_error(f"Fetch lead from Facebook failed: {str(e)}")
		return {}

def create_lead(lead_data, field_map):
	"""Create ERPNext Lead from Facebook lead data"""
	try:
		lead = frappe.new_doc("Lead")
		
		# Map fields based on field_map
		field_data = {item["name"]: item["values"][0] for item in lead_data.get("field_data", [])}
		
		for fb_field, erp_field in field_map.items():
			if fb_field in field_data and hasattr(lead, erp_field):
				setattr(lead, erp_field, field_data[fb_field])
		
		# Set default values
		settings = frappe.get_single("Facebook Settings")
		if settings.default_lead_owner:
			lead.lead_owner = settings.default_lead_owner
		
		lead.source = "Facebook"
		lead.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return lead
		
	except Exception as e:
		frappe.log_error(f"Create lead failed: {str(e)}")
		frappe.throw(_(f"Failed to create lead: {str(e)}"))

def create_contact(lead_data, field_map):
	"""Create ERPNext Contact from Facebook lead data"""
	try:
		contact = frappe.new_doc("Contact")
		
		# Map fields based on field_map
		field_data = {item["name"]: item["values"][0] for item in lead_data.get("field_data", [])}
		
		for fb_field, erp_field in field_map.items():
			if fb_field in field_data and hasattr(contact, erp_field):
				setattr(contact, erp_field, field_data[fb_field])
		
		contact.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return contact
		
	except Exception as e:
		frappe.log_error(f"Create contact failed: {str(e)}")
		frappe.throw(_(f"Failed to create contact: {str(e)}"))

def create_customer(lead_data, field_map):
	"""Create ERPNext Customer from Facebook lead data"""
	try:
		customer = frappe.new_doc("Customer")
		
		# Map fields based on field_map
		field_data = {item["name"]: item["values"][0] for item in lead_data.get("field_data", [])}
		
		for fb_field, erp_field in field_map.items():
			if fb_field in field_data and hasattr(customer, erp_field):
				setattr(customer, erp_field, field_data[fb_field])
		
		customer.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return customer
		
	except Exception as e:
		frappe.log_error(f"Create customer failed: {str(e)}")
		frappe.throw(_(f"Failed to create customer: {str(e)}"))

@frappe.whitelist()
def get_unmapped_leads(limit=50):
	"""Get unmapped Facebook leads"""
	try:
		leads = frappe.get_list(
			"Facebook Lead Log",
			filters={"synced": 0},
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