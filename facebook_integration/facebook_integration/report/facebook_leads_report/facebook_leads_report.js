frappe.query_reports["Facebook Leads Report"] = {
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
			"fieldname": "synced",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nPending\nConverted",
			"default": ""
		}
	]
}