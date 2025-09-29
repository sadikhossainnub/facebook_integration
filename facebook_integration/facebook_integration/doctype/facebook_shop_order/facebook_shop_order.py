import frappe
from frappe.model.document import Document

class FacebookShopOrder(Document):
	def after_insert(self):
		if not self.sales_order:
			frappe.enqueue("facebook_integration.api.shop.create_sales_order", order_id=self.name)
	
	def create_sales_order(self):
		if self.sales_order:
			return
		
		# Create or get customer
		customer = self.get_or_create_customer()
		
		# Create sales order
		so = frappe.new_doc("Sales Order")
		so.customer = customer
		so.delivery_date = frappe.utils.add_days(self.order_date, 7)
		so.company = frappe.db.get_value("Facebook Account", self.facebook_account, "company")
		
		for item in self.items:
			so.append("items", {
				"item_code": item.item_code,
				"qty": item.qty,
				"rate": item.rate
			})
		
		so.insert()
		so.submit()
		
		self.sales_order = so.name
		self.status = "Synced"
		self.save()
	
	def get_or_create_customer(self):
		if self.customer:
			return self.customer
		
		customer_name = f"FB-{self.customer_name}"
		if frappe.db.exists("Customer", customer_name):
			return customer_name
		
		customer = frappe.new_doc("Customer")
		customer.customer_name = self.customer_name
		customer.customer_type = "Individual"
		if self.customer_email:
			customer.email_id = self.customer_email
		if self.customer_phone:
			customer.mobile_no = self.customer_phone
		customer.insert()
		
		self.customer = customer.name
		return customer.name