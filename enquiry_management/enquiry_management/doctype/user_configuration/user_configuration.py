# Copyright (c) 2026, Vivek Choudhary and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import get_root_of
from frappe.model.document import Document


class UserConfiguration(Document):
	pass


@frappe.whitelist()
def segment_level2_query(doctype, txt, searchfield, start, page_len, filters):
	"""Return only level 2 segments (children of root)."""
	root = get_root_of("Segment")
	if not root:
		return []
	return frappe.db.sql(
		"""
		SELECT s.name
		FROM `tabSegment` s
		WHERE s.parent_segment = %(root)s
		  AND s.name LIKE %(txt)s
		ORDER BY s.name
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"root": root,
			"txt": f"%{txt}%",
			"start": start,
			"page_len": page_len,
		},
	)


@frappe.whitelist()
def segment_level3_query(doctype, txt, searchfield, start, page_len, filters):
	"""Return only level 3 segments, optionally filtered by level 2 parents."""
	filters = frappe._dict(filters or {})
	parents = filters.get("parents") or []
	root = get_root_of("Segment")
	if not root:
		return []

	parent_filter = ""
	params = {
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len,
	}

	if parents:
		parent_filter = " AND s.parent_segment IN %(parents)s"
		params["parents"] = tuple(parents)

	return frappe.db.sql(
		f"""
		SELECT s.name
		FROM `tabSegment` s
		LEFT JOIN `tabSegment` p ON p.name = s.parent_segment
		WHERE p.parent_segment = %(root)s
		  AND s.name LIKE %(txt)s
		  {parent_filter}
		ORDER BY s.name
		LIMIT %(start)s, %(page_len)s
		""",
		{**params, "root": root},
	)
