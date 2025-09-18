import frappe
from frappe.utils import today, get_datetime

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
		# Generate webhook URL if not set
		if settings and not settings.webhook_url:
			site_url = frappe.utils.get_url()
			settings.webhook_url = f"{site_url}/api/method/facebook_integration.api.webhook"
	except:
		context.settings = None
	
	# Get statistics
	context.stats = get_facebook_stats()
	
	# Get recent messages
	try:
		context.recent_messages = frappe.get_list(
			"Facebook Message Log",
			fields=["name", "sender_name", "content", "direction", "status", "received_at", "sent_at"],
			order_by="creation desc",
			limit=10
		)
		# Format timestamps
		for message in context.recent_messages:
			timestamp = message.get('received_at') or message.get('sent_at')
			if timestamp:
				message['formatted_time'] = frappe.utils.pretty_date(timestamp)
	except:
		context.recent_messages = []
	
	# Get unmapped leads
	try:
		context.unmapped_leads = frappe.get_list(
			"Facebook Lead Log",
			filters={"synced": 0},
			fields=["name", "fb_leadgen_id", "created_at"],
			order_by="created_at desc",
			limit=10
		)
		# Format timestamps
		for lead in context.unmapped_leads:
			if lead.get('created_at'):
				lead['formatted_time'] = frappe.utils.pretty_date(lead['created_at'])
	except:
		context.unmapped_leads = []
	
	return context

def get_facebook_stats():
	"""Get Facebook integration statistics"""
	stats = {
		'total_messages': 0,
		'total_leads': 0,
		'unmapped_leads': 0,
		'today_messages': 0
	}
	
	try:
		# Total messages
		stats['total_messages'] = frappe.db.count('Facebook Message Log')
		
		# Total leads
		stats['total_leads'] = frappe.db.count('Facebook Lead Log')
		
		# Unmapped leads
		stats['unmapped_leads'] = frappe.db.count('Facebook Lead Log', {'synced': 0})
		
		# Today's messages
		today_start = get_datetime(today())
		stats['today_messages'] = frappe.db.count('Facebook Message Log', {
			'creation': ['>=', today_start]
		})
		
	except Exception as e:
		frappe.log_error(f"Error getting Facebook stats: {str(e)}")
	
	return stats