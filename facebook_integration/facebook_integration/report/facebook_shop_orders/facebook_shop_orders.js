frappe.query_reports["Facebook Shop Orders"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date", 
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "facebook_account",
			"label": __("Facebook Account"),
			"fieldtype": "Link",
			"options": "Facebook Account"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nPending\nProcessing\nShipped\nDelivered\nCancelled\nSynced"
		}
	]
}