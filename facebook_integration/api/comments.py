import frappe
import requests

@frappe.whitelist()
def sync_post_comments(account_name, post_id):
	"""Sync comments for a Facebook post"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		
		url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
		params = {
			"fields": "id,message,from,created_time,like_count,comment_count,attachment",
			"access_token": account.get_password("access_token")
		}
		
		response = requests.get(url, params=params)
		if response.status_code != 200:
			return {"success": False, "error": "Failed to fetch comments"}
		
		data = response.json()
		synced_count = 0
		
		for comment in data.get("data", []):
			if create_comment_log(account_name, post_id, comment):
				synced_count += 1
		
		return {"success": True, "synced_count": synced_count}
		
	except Exception as e:
		frappe.log_error(f"Comment sync failed: {str(e)}")
		return {"success": False, "error": str(e)}

def create_comment_log(account_name, post_id, comment_data):
	"""Create Comment Log from Facebook comment data"""
	try:
		comment_id = comment_data.get("id")
		
		# Skip if already exists
		if frappe.db.exists("Comment Log", {"comment_id": comment_id}):
			return False
		
		from_data = comment_data.get("from", {})
		
		comment_log = frappe.new_doc("Comment Log")
		comment_log.facebook_account = account_name
		comment_log.post_id = post_id
		comment_log.comment_id = comment_id
		comment_log.commenter_id = from_data.get("id")
		comment_log.commenter_name = from_data.get("name")
		comment_log.message = comment_data.get("message", "")
		comment_log.created_time = comment_data.get("created_time")
		comment_log.like_count = comment_data.get("like_count", 0)
		comment_log.reply_count = comment_data.get("comment_count", 0)
		
		if "attachment" in comment_data:
			comment_log.attachment_url = comment_data["attachment"].get("media", {}).get("image", {}).get("src")
		
		comment_log.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return True
		
	except Exception as e:
		frappe.log_error(f"Comment log creation failed: {str(e)}")
		return False

@frappe.whitelist()
def reply_to_comment(account_name, comment_id, message):
	"""Reply to a Facebook comment"""
	try:
		account = frappe.get_doc("Facebook Account", account_name)
		
		url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
		data = {
			"message": message,
			"access_token": account.get_password("access_token")
		}
		
		response = requests.post(url, data=data)
		if response.status_code == 200:
			reply_data = response.json()
			
			# Create comment log for reply
			reply_comment = {
				"id": reply_data.get("id"),
				"message": message,
				"from": {"id": account.page_id, "name": account.page_name},
				"created_time": frappe.utils.now()
			}
			
			# Get original comment to find post_id
			original_comment = frappe.get_value("Comment Log", {"comment_id": comment_id}, "post_id")
			if original_comment:
				create_comment_log(account_name, original_comment, reply_comment)
			
			return {"success": True, "reply_id": reply_data.get("id")}
		else:
			return {"success": False, "error": "Failed to post reply"}
			
	except Exception as e:
		frappe.log_error(f"Comment reply failed: {str(e)}")
		return {"success": False, "error": str(e)}

def handle_comment_webhook(account_name, comment_data):
	"""Handle comment webhook from Facebook"""
	try:
		post_id = comment_data.get("post_id")
		comment_id = comment_data.get("comment_id")
		
		if not post_id or not comment_id:
			return
		
		# Fetch comment details from Facebook API
		account = frappe.get_doc("Facebook Account", account_name)
		url = f"https://graph.facebook.com/v18.0/{comment_id}"
		params = {
			"fields": "id,message,from,created_time,like_count,comment_count,attachment",
			"access_token": account.get_password("access_token")
		}
		
		response = requests.get(url, params=params)
		if response.status_code == 200:
			comment_details = response.json()
			create_comment_log(account_name, post_id, comment_details)
			
	except Exception as e:
		frappe.log_error(f"Comment webhook handling failed: {str(e)}")