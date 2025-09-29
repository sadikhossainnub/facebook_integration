import frappe
import requests
from frappe import _

@frappe.whitelist()
def sync_products(account_name):
	"""Sync products from Facebook Shop to ERPNext"""
	account = frappe.get_doc("Facebook Account", account_name)
	if not account.enable_shop:
		return {"status": "error", "message": "Shop integration not enabled"}
	
	try:
		# Get products from Facebook
		url = f"https://graph.facebook.com/v18.0/{account.page_id}/products"
		params = {
			"access_token": account.get_password("access_token"),
			"fields": "id,name,description,price,currency,availability,image_url"
		}
		
		response = requests.get(url, params=params)
		data = response.json()
		
		if "error" in data:
			return {"status": "error", "message": data["error"]["message"]}
		
		synced_count = 0
		for product in data.get("data", []):
			sync_single_product(account, product)
			synced_count += 1
		
		return {"status": "success", "synced": synced_count}
		
	except Exception as e:
		frappe.log_error(f"Facebook Shop Sync Error: {str(e)}")
		return {"status": "error", "message": str(e)}

def sync_single_product(account, product_data):
	"""Sync single product to ERPNext Item"""
	item_code = f"FB-{product_data['id']}"
	
	if frappe.db.exists("Item", item_code):
		item = frappe.get_doc("Item", item_code)
	else:
		item = frappe.new_doc("Item")
		item.item_code = item_code
		item.item_group = "Facebook Products"
	
	item.item_name = product_data.get("name", "")
	item.description = product_data.get("description", "")
	item.standard_rate = float(product_data.get("price", 0)) / 100  # Facebook price in cents
	item.is_sales_item = 1
	item.facebook_product_id = product_data["id"]
	
	item.save()
	return item

@frappe.whitelist()
def create_sales_order(order_id):
	"""Create Sales Order from Facebook Shop Order"""
	order = frappe.get_doc("Facebook Shop Order", order_id)
	order.create_sales_order()

@frappe.whitelist()
def sync_inventory(account_name):
	"""Sync inventory from ERPNext to Facebook Shop"""
	account = frappe.get_doc("Facebook Account", account_name)
	if not account.enable_shop:
		return {"status": "error", "message": "Shop integration not enabled"}
	
	# Get items with Facebook product IDs
	items = frappe.get_all("Item", 
		filters={"facebook_product_id": ["!=", ""]},
		fields=["name", "facebook_product_id"]
	)
	
	updated_count = 0
	for item in items:
		# Get current stock
		stock_qty = frappe.db.get_value("Bin", 
			{"item_code": item.name, "warehouse": account.default_warehouse}, 
			"actual_qty") or 0
		
		# Update Facebook inventory
		update_facebook_inventory(account, item.facebook_product_id, stock_qty)
		updated_count += 1
	
	return {"status": "success", "updated": updated_count}

def update_facebook_inventory(account, product_id, qty):
	"""Update inventory on Facebook"""
	url = f"https://graph.facebook.com/v18.0/{product_id}"
	data = {
		"access_token": account.get_password("access_token"),
		"inventory": int(qty)
	}
	
	response = requests.post(url, data=data)
	return response.json()

def handle_order_webhook(account_name, order_data):
	"""Handle Facebook Shop order webhook"""
	try:
		order_id = order_data.get("id")
		
		# Check if order already exists
		if frappe.db.exists("Facebook Shop Order", {"facebook_order_id": order_id}):
			return
		
		# Create shop order record
		shop_order = frappe.new_doc("Facebook Shop Order")
		shop_order.facebook_account = account_name
		shop_order.facebook_order_id = order_id
		shop_order.customer_name = order_data.get("buyer_name", "Facebook Customer")
		shop_order.customer_email = order_data.get("buyer_email")
		shop_order.total_amount = float(order_data.get("total_amount", 0)) / 100
		shop_order.currency = order_data.get("currency", "USD")
		shop_order.order_date = order_data.get("created_time")
		shop_order.status = "Pending"
		
		# Add order items
		for item_data in order_data.get("items", []):
			shop_order.append("items", {
				"facebook_product_id": item_data.get("product_id"),
				"item_name": item_data.get("product_name"),
				"qty": item_data.get("quantity", 1),
				"rate": float(item_data.get("price", 0)) / 100
			})
		
		shop_order.insert(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(f"Shop order webhook handling failed: {str(e)}")