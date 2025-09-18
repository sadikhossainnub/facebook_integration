import frappe

def after_install():
	"""Setup Facebook Integration after installation"""
	
	# Create custom roles
	create_facebook_roles()
	
	# Setup default permissions
	setup_permissions()
	
	# Create workspace and dashboard
	create_workspace_and_dashboard()
	
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

def create_workspace_and_dashboard():
	"""Create Facebook Integration workspace and dashboard charts"""
	
	# Create workspace if it doesn't exist
	if not frappe.db.exists("Workspace", "Facebook Integration"):
		workspace = frappe.get_doc({
			"doctype": "Workspace",
			"label": "Facebook Integration",
			"title": "Facebook Integration",
			"icon": "facebook",
			"module": "Facebook Integration",
			"is_standard": 1,
			"public": 1
		})
		workspace.insert(ignore_permissions=True)
	
	# Create basic dashboard charts
	try:
		if not frappe.db.exists("Dashboard Chart", "Facebook Messages"):
			chart = frappe.get_doc({
				"doctype": "Dashboard Chart",
				"chart_name": "Facebook Messages",
				"chart_type": "Line",
				"document_type": "Facebook Message Log",
				"group_by_based_on": "creation",
				"group_by_type": "Count",
				"time_interval": "Daily",
				"timeseries": 1,
				"is_public": 1,
				"module": "Facebook Integration"
			})
			chart.insert(ignore_permissions=True)
	except Exception:
		pass