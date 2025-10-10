import frappe
from frappe.model.document import Document

class CommentLog(Document):
	def validate(self):
		if self.comment_id:
			existing = frappe.db.exists("Comment Log", {"comment_id": self.comment_id, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Comment with ID {self.comment_id} already exists")