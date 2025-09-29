import frappe

def after_install():
	"""Setup after app installation"""
	create_custom_roles()
	create_item_group()
	setup_permissions()

def create_custom_roles():
	"""Create Facebook-specific roles"""
	roles = [
		{
			"role_name": "Facebook Admin",
			"description": "Full access to Facebook Integration features"
		},
		{
			"role_name": "Facebook Agent", 
			"description": "Handle Facebook messages and leads"
		},
		{
			"role_name": "Facebook Manager",
			"description": "View Facebook reports and analytics"
		}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.new_doc("Role")
			role.role_name = role_data["role_name"]
			role.description = role_data["description"]
			role.insert(ignore_permissions=True)

def create_item_group():
	"""Create Facebook Products item group"""
	if not frappe.db.exists("Item Group", "Facebook Products"):
		item_group = frappe.new_doc("Item Group")
		item_group.item_group_name = "Facebook Products"
		item_group.parent_item_group = "All Item Groups"
		item_group.is_group = 0
		item_group.insert(ignore_permissions=True)

def setup_permissions():
	"""Setup role-based permissions"""
	# Facebook Agent permissions
	agent_permissions = [
		{"doctype": "Facebook Message Log", "role": "Facebook Agent", "read": 1, "write": 1, "create": 1},
		{"doctype": "Facebook Lead Log", "role": "Facebook Agent", "read": 1, "write": 1},
		{"doctype": "Lead", "role": "Facebook Agent", "read": 1, "write": 1, "create": 1},
		{"doctype": "Contact", "role": "Facebook Agent", "read": 1, "write": 1, "create": 1},
		{"doctype": "Communication", "role": "Facebook Agent", "read": 1, "write": 1, "create": 1}
	]
	
	# Facebook Manager permissions  
	manager_permissions = [
		{"doctype": "Facebook Campaign Metric", "role": "Facebook Manager", "read": 1},
		{"doctype": "Facebook Shop Order", "role": "Facebook Manager", "read": 1},
		{"doctype": "Facebook Account", "role": "Facebook Manager", "read": 1}
	]
	
	all_permissions = agent_permissions + manager_permissions
	
	for perm in all_permissions:
		if not frappe.db.exists("Custom DocPerm", {
			"parent": perm["doctype"],
			"role": perm["role"]
		}):
			doc_perm = frappe.new_doc("Custom DocPerm")
			doc_perm.parent = perm["doctype"]
			doc_perm.parenttype = "DocType"
			doc_perm.parentfield = "permissions"
			doc_perm.role = perm["role"]
			doc_perm.read = perm.get("read", 0)
			doc_perm.write = perm.get("write", 0)
			doc_perm.create = perm.get("create", 0)
			doc_perm.insert(ignore_permissions=True)