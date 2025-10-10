import frappe

def execute():
    """Add Facebook Messenger ID fields to Lead and Contact"""
    
    # Add Facebook Messenger ID to Lead
    if not frappe.db.exists("Custom Field", {"dt": "Lead", "fieldname": "facebook_messenger_id"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Lead",
            "fieldname": "facebook_messenger_id",
            "label": "Facebook Messenger ID",
            "fieldtype": "Data",
            "insert_after": "source",
            "read_only": 1,
            "unique": 1
        }).insert()
    
    # Add Facebook Messenger ID to Contact
    if not frappe.db.exists("Custom Field", {"dt": "Contact", "fieldname": "facebook_messenger_id"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Contact",
            "fieldname": "facebook_messenger_id",
            "label": "Facebook Messenger ID",
            "fieldtype": "Data",
            "insert_after": "mobile_no",
            "read_only": 1,
            "unique": 1
        }).insert()
    
    # Add Facebook Messenger as Communication Medium
    if not frappe.db.exists("Communication Medium Type", "Facebook Messenger"):
        frappe.get_doc({
            "doctype": "Communication Medium Type",
            "communication_medium_type": "Facebook Messenger"
        }).insert()
    
    frappe.db.commit()