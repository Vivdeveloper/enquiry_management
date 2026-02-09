# Copyright (c) 2026, Vivek Choudhary and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint
from frappe.model.document import Document


class Segment(Document):
	def validate(self):
		self.validate_tree_depth()

	def validate_tree_depth(self):
		"""Allow only 4 levels: Segment > Sub Segment > Sub Sub Segment > Level 4.
		Level 4 cannot be a group and cannot have children."""
		if not self.parent_segment:
			# Level 1 (root) — always allowed
			if not cint(self.is_group):
				frappe.throw("Level 1 is not allowed when is_group = 0.")
			return

		# Count depth by walking up the tree
		depth = 1
		parent = self.parent_segment
		while parent:
			depth += 1
			if depth > 4:
				frappe.throw(
					"Maximum 4 levels allowed: Segment → Sub Segment → Sub Sub Segment → Level 4"
				)
			parent = frappe.db.get_value("Segment", parent, "parent_segment")

		# Level 4 cannot be a group
		if depth == 2 and not cint(self.is_group):
			frappe.throw("Level 2 is not allowed when is_group = 0.")
		if depth == 3 and cint(self.is_group):
			frappe.throw("Level 3 is not allowed when is_group = 1.")
		if depth == 4 and cint(self.is_group):
			frappe.throw("Level 4 is not allowed when is_group = 1.")

		# Level 4 cannot have children
		if depth == 4 and self.name:
			if frappe.db.exists("Segment", {"parent_segment": self.name}):
				frappe.throw("Level 4 cannot have children.")
