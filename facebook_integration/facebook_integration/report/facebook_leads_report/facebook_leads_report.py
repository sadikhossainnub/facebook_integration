import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Date"),
			"fieldname": "created_at",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Facebook Account"),
			"fieldname": "facebook_account",
			"fieldtype": "Link",
			"options": "Facebook Account",
			"width": 150
		},
		{
			"label": _("Full Name"),
			"fieldname": "full_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Email"),
			"fieldname": "email",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Phone"),
			"fieldname": "phone",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Mapped To"),
			"fieldname": "mapped_document",
			"fieldtype": "Dynamic Link",
			"options": "mapped_to",
			"width": 150
		},
		{
			"label": _("Lead Owner"),
			"fieldname": "lead_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 150
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			DATE(fll.created_at) as created_at,
			fll.facebook_account,
			fll.full_name,
			fll.email,
			fll.phone,
			CASE 
				WHEN fll.synced = 1 THEN 'Converted'
				ELSE 'Pending'
			END as status,
			fll.mapped_document,
			COALESCE(l.lead_owner, c.owner, cu.owner) as lead_owner
		FROM `tabFacebook Lead Log` fll
		LEFT JOIN `tabLead` l ON fll.lead = l.name
		LEFT JOIN `tabContact` c ON fll.contact = c.name  
		LEFT JOIN `tabCustomer` cu ON fll.customer = cu.name
		{conditions}
		ORDER BY fll.created_at DESC
	""", filters, as_dict=1)
	
	return data

def get_conditions(filters):
	conditions = "WHERE 1=1"
	
	if filters.get("from_date"):
		conditions += " AND DATE(fll.created_at) >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND DATE(fll.created_at) <= %(to_date)s"
	
	if filters.get("facebook_account"):
		conditions += " AND fll.facebook_account = %(facebook_account)s"
	
	if filters.get("synced"):
		conditions += " AND fll.synced = %(synced)s"
	
	return conditions