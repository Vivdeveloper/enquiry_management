# Copyright (c) 2026, Vivek Choudhary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UserConfiguration(Document):
	pass


@frappe.whitelist()
def get_user_roles(user):
	"""Return roles for a given user."""
	if not user:
		return []
	return frappe.get_roles(user)
