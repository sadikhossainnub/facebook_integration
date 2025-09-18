import frappe

def get_context(context):
	"""Get context for Facebook Integration page"""
	
	# Check permissions
	if not frappe.has_permission("Facebook Settings", "read"):
		frappe.throw("Not permitted", frappe.PermissionError)
	
	context.no_cache = 1
	context.show_sidebar = True
	
	# Get Facebook Settings
	try:
		settings = frappe.get_single("Facebook Settings")
		context.settings = settings
	except:
		context.settings = None
	
	# Get recent messages
	try:
		context.recent_messages = frappe.get_list(
			"Facebook Message Log",
			fields=["name", "sender_name", "content", "direction", "status", "received_at", "sent_at"],
			order_by="creation desc",
			limit=10
		)
	except:
		context.recent_messages = []
	
	# Get unmapped leads
	try:
		context.unmapped_leads = frappe.get_list(
			"Facebook Lead Log",
			filters={"synced": 0},
			fields=["name", "fb_leadgen_id", "created_at"],
			order_by="created_at desc",
			limit=5
		)
	except:
		context.unmapped_leads = []
	
	return context