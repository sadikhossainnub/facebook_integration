import frappe

def after_install():
	"""Setup Facebook Integration after installation"""
	
	# Create custom roles
	create_facebook_roles()
	
	# Setup default permissions
	setup_permissions()
	
	frappe.db.commit()

def create_facebook_roles():
	"""Create Facebook Integration specific roles"""
	
	roles = [
		{
			"role_name": "Facebook Admin",
			"description": "Full access to Facebook Integration settings and data"
		},
		{
			"role_name": "Facebook Agent", 
			"description": "Access to Facebook messages and lead mapping"
		}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.new_doc("Role")
			role.role_name = role_data["role_name"]
			role.description = role_data["description"]
			role.insert(ignore_permissions=True)

def setup_permissions():
	"""Setup default permissions for Facebook Integration doctypes"""
	
	# Facebook Admin permissions
	admin_permissions = [
		{
			"doctype": "Facebook Settings",
			"role": "Facebook Admin",
			"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
		},
		{
			"doctype": "Facebook Message Log", 
			"role": "Facebook Admin",
			"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
		},
		{
			"doctype": "Facebook Lead Log",
			"role": "Facebook Admin", 
			"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
		},
		{
			"doctype": "Facebook Campaign Metric",
			"role": "Facebook Admin",
			"perms": {"read": 1, "write": 1, "create": 1, "delete": 1}
		}
	]
	
	# Facebook Agent permissions
	agent_permissions = [
		{
			"doctype": "Facebook Message Log",
			"role": "Facebook Agent", 
			"perms": {"read": 1, "write": 1, "create": 1}
		},
		{
			"doctype": "Facebook Lead Log",
			"role": "Facebook Agent",
			"perms": {"read": 1, "write": 1}
		}
	]
	
	all_permissions = admin_permissions + agent_permissions
	
	for perm_data in all_permissions:
		# Check if permission already exists
		existing = frappe.db.exists("Custom DocPerm", {
			"parent": perm_data["doctype"],
			"role": perm_data["role"]
		})
		
		if not existing:
			perm = frappe.new_doc("Custom DocPerm")
			perm.parent = perm_data["doctype"]
			perm.parenttype = "DocType"
			perm.parentfield = "permissions"
			perm.role = perm_data["role"]
			
			for perm_type, value in perm_data["perms"].items():
				setattr(perm, perm_type, value)
			
			perm.insert(ignore_permissions=True)