import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Order Date"),
			"fieldname": "order_date",
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
			"label": _("Facebook Order ID"),
			"fieldname": "facebook_order_id",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Customer"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Email"),
			"fieldname": "customer_email",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 150
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	
	data = frappe.db.sql(f"""
		SELECT 
			DATE(order_date) as order_date,
			facebook_account,
			facebook_order_id,
			customer_name,
			customer_email,
			total_amount,
			status,
			sales_order
		FROM `tabFacebook Shop Order`
		{conditions}
		ORDER BY order_date DESC
	""", filters, as_dict=1)
	
	return data

def get_conditions(filters):
	conditions = "WHERE 1=1"
	
	if filters.get("from_date"):
		conditions += " AND DATE(order_date) >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND DATE(order_date) <= %(to_date)s"
	
	if filters.get("facebook_account"):
		conditions += " AND facebook_account = %(facebook_account)s"
	
	if filters.get("status"):
		conditions += " AND status = %(status)s"
	
	return conditions