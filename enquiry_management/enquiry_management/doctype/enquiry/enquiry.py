# Copyright (c) 2026, Vivek Choudhary and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Enquiry(Document):
	def validate(self):
		self.check_edit_permission()

	def before_cancel(self):
		if self.workflow_state == "Regret":
			frappe.throw("Cancellation is not allowed when Workflow State is 'Regret'.")

	def check_edit_permission(self):
		"""Only current_owner or System Manager can edit"""
		# Skip for new documents
		if self.is_new():
			return

		# Allow Administrator
		if frappe.session.user == "Administrator":
			return

		# Allow System Manager
		if "System Manager" in frappe.get_roles(frappe.session.user):
			return

		# Allow current_owner
		if self.current_owner == frappe.session.user:
			return
		# Allow previous current_owner to change owner
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.current_owner == frappe.session.user:
			return

		# Deny all others
		frappe.throw(
			"You can only view this enquiry. Only the Current Owner or System Manager can edit.",
			frappe.PermissionError
		)


def get_permission_query_conditions(user):
	"""
	Permission query for Enquiry.
	If self_creator = 1:
		- created_by + segment/sub_segment/org must match, OR
		- assigned_user (no restriction)
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return None

	escaped_user = frappe.db.escape(user)

	# Segment match subquery
	segment_match = f"""
		`tabEnquiry`.`segment` IN (
			SELECT `segment`
			FROM `tabUser Configuration Segment`
			WHERE `parent` IN (
				SELECT `name` FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `self_creator` = 1
			)
		)
	"""

	# Sub-segment match subquery
	sub_segment_match = f"""
		`tabEnquiry`.`sub_segment` IN (
			SELECT `sub_segment`
			FROM `tabUser Configuration Sub Segment`
			WHERE `parent` IN (
				SELECT `name` FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `self_creator` = 1
			)
		)
	"""

	# Organisation match subquery
	org_match = f"""
		(
			`tabEnquiry`.`primary_organisation` IN (
				SELECT `primary_organisation`
				FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `self_creator` = 1
			)
			OR `tabEnquiry`.`primary_organisation` IN (
				SELECT `organisation`
				FROM `tabUser Configuration Organisation`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user} AND `self_creator` = 1
				)
			)
		)
	"""

	# Assigned user check subquery
	is_assigned = f"""
		`tabEnquiry`.`name` IN (
			SELECT `parent`
			FROM `tabAssignment Log`
			WHERE `assigned_user` = {escaped_user}
			AND `parenttype` = 'Enquiry'
		)
	"""

	# Reporting tos - current user can see all data from users who report to them
	reporting_tos_match = f"""
		`tabEnquiry`.`created_by` IN (
			SELECT uc.`user`
			FROM `tabUser Configuration` uc
			WHERE uc.`name` IN (
				SELECT `parent`
				FROM `tabUser Configuration Reporting To`
				WHERE `reporting_to` = {escaped_user}
			)
		)
	"""

	# Head - can see all enquiries matching their segments
	head_segment_match = f"""
		`tabEnquiry`.`segment` IN (
			SELECT `segment`
			FROM `tabUser Configuration Segment`
			WHERE `parent` IN (
				SELECT `name` FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `head` = 1
			)
		)
	"""

	# Head - can see all enquiries matching their sub_segments
	head_sub_segment_match = f"""
		`tabEnquiry`.`sub_segment` IN (
			SELECT `sub_segment`
			FROM `tabUser Configuration Sub Segment`
			WHERE `parent` IN (
				SELECT `name` FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `head` = 1
			)
		)
	"""

	# Head - can see all enquiries matching their primary_organisation and organisations
	head_org_match = f"""
		(
			`tabEnquiry`.`primary_organisation` IN (
				SELECT `primary_organisation`
				FROM `tabUser Configuration`
				WHERE `user` = {escaped_user} AND `head` = 1
			)
			OR `tabEnquiry`.`primary_organisation` IN (
				SELECT `organisation`
				FROM `tabUser Configuration Organisation`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user} AND `head` = 1
				)
			)
		)
	"""

	return f"""(
		/* created_by + segment */
		(`tabEnquiry`.`created_by` = {escaped_user} AND {segment_match})
		/* created_by + sub_segment */
		OR (`tabEnquiry`.`created_by` = {escaped_user} AND {sub_segment_match})
		/* created_by + org */
		OR (`tabEnquiry`.`created_by` = {escaped_user} AND {org_match})
		/* assigned_user - no restriction */
		OR ({is_assigned})
		/* reporting_tos - can see all data from users who report to them */
		OR ({reporting_tos_match})
		/* head - can see all enquiries matching their segments */
		OR ({head_segment_match})
		/* head - can see all enquiries matching their sub_segments */
		OR ({head_sub_segment_match})
		/* head - can see all enquiries matching their organisations */
		OR ({head_org_match})
	)"""


@frappe.whitelist()
def get_permission_info():
	"""Get permission info for the current user"""
	user = frappe.session.user
	permissions = []

	if user == "Administrator":
		return {"user": user, "permissions": ["Full Access (Administrator)"]}

	# Check User Configuration
	user_config = frappe.db.get_value(
		"User Configuration",
		{"user": user},
		["name", "self_creator", "head", "primary_organisation"],
		as_dict=True
	)

	if not user_config:
		permissions.append("No User Configuration found - limited access")
		return {"user": user, "permissions": permissions}

	# Self creator permissions
	if user_config.self_creator:
		permissions.append("Self Creator: Can see own created enquiries matching segments/sub-segments/organisations")

		# Get segments
		segments = frappe.get_all(
			"User Configuration Segment",
			filters={"parent": user_config.name},
			pluck="segment",
			ignore_permissions=True
		)
		if segments:
			permissions.append(f"  - Segments: {', '.join(segments)}")

		# Get sub-segments
		sub_segments = frappe.get_all(
			"User Configuration Sub Segment",
			filters={"parent": user_config.name},
			pluck="sub_segment",
			ignore_permissions=True
		)
		if sub_segments:
			permissions.append(f"  - Sub Segments: {', '.join(sub_segments)}")

		# Get organisations
		orgs = frappe.get_all(
			"User Configuration Organisation",
			filters={"parent": user_config.name},
			pluck="organisation",
			ignore_permissions=True
		)
		if user_config.primary_organisation:
			orgs.insert(0, user_config.primary_organisation)
		if orgs:
			permissions.append(f"  - Organisations: {', '.join(orgs)}")

	# Head permissions
	if user_config.head:
		permissions.append("Head: Can see all enquiries matching segments/sub-segments/organisations")

		# Get segments for head
		head_segments = frappe.get_all(
			"User Configuration Segment",
			filters={"parent": user_config.name},
			pluck="segment",
			ignore_permissions=True
		)
		if head_segments:
			permissions.append(f"  - Segments: {', '.join(head_segments)}")
		else:
			permissions.append("  - Segments: None configured")

		# Get sub-segments for head
		head_sub_segments = frappe.get_all(
			"User Configuration Sub Segment",
			filters={"parent": user_config.name},
			pluck="sub_segment",
			ignore_permissions=True
		)
		if head_sub_segments:
			permissions.append(f"  - Sub Segments: {', '.join(head_sub_segments)}")
		else:
			permissions.append("  - Sub Segments: None configured")

		# Get organisations for head
		head_orgs = []
		if user_config.primary_organisation:
			head_orgs.append(user_config.primary_organisation)

		# Get multiple organisations from child table
		child_orgs = frappe.get_all(
			"User Configuration Organisation",
			filters={"parent": user_config.name},
			pluck="organisation",
			ignore_permissions=True
		)
		head_orgs.extend(child_orgs)

		if head_orgs:
			permissions.append(f"  - Organisations: {', '.join(head_orgs)}")
		else:
			permissions.append("  - Organisations: None configured")

	# Assignment Log - show assigned enquiries count
	assigned_count = frappe.db.count(
		"Assignment Log",
		{"assigned_user": user, "parenttype": "Enquiry"}
	)
	if assigned_count:
		permissions.append(f"Assigned Enquiries: {assigned_count} enquiries assigned to you")
	else:
		permissions.append("Assigned Enquiries: No enquiries assigned to you")

	# Reporting To - users who report to current user
	reporting_users = frappe.db.sql("""
		SELECT uc.user
		FROM `tabUser Configuration` uc
		WHERE uc.name IN (
			SELECT parent
			FROM `tabUser Configuration Reporting To`
			WHERE reporting_to = %s
		)
	""", user, as_dict=True)

	if reporting_users:
		user_list = [r.user for r in reporting_users]
		permissions.append(f"Reporting To You: Can see enquiries from {', '.join(user_list)}")

	return {"user": user, "permissions": permissions}


@frappe.whitelist()
def get_user_filter_options():
	"""Get filter options based on user configuration"""
	user = frappe.session.user
	result = {
		"segments": [],
		"sub_segments": [],
		"organisations": [],
		"reporting_users": []
	}

	if user == "Administrator":
		# Return all options for Administrator
		result["segments"] = frappe.get_all("Segment", pluck="name", ignore_permissions=True)
		result["sub_segments"] = frappe.get_all("Sub Segment", pluck="name", ignore_permissions=True)
		result["organisations"] = frappe.get_all("Organisation", pluck="name", ignore_permissions=True)
		return result

	# Get User Configuration
	user_config = frappe.db.get_value(
		"User Configuration",
		{"user": user},
		["name", "primary_organisation"],
		as_dict=True
	)

	if not user_config:
		return result

	# Get segments
	result["segments"] = frappe.get_all(
		"User Configuration Segment",
		filters={"parent": user_config.name},
		pluck="segment",
		ignore_permissions=True
	)

	# Get sub-segments
	result["sub_segments"] = frappe.get_all(
		"User Configuration Sub Segment",
		filters={"parent": user_config.name},
		pluck="sub_segment",
		ignore_permissions=True
	)

	# Get organisations
	orgs = []
	if user_config.primary_organisation:
		orgs.append(user_config.primary_organisation)
	child_orgs = frappe.get_all(
		"User Configuration Organisation",
		filters={"parent": user_config.name},
		pluck="organisation",
		ignore_permissions=True
	)
	orgs.extend(child_orgs)
	result["organisations"] = orgs

	# Get users who report to current user
	reporting_users = frappe.db.sql("""
		SELECT uc.user
		FROM `tabUser Configuration` uc
		WHERE uc.name IN (
			SELECT parent
			FROM `tabUser Configuration Reporting To`
			WHERE reporting_to = %s
		)
	""", user, as_dict=True)
	result["reporting_users"] = [r.user for r in reporting_users]

	return result


@frappe.whitelist()
def get_assigned_enquiries():
	"""Get enquiries assigned to the current user"""
	user = frappe.session.user

	assigned_enquiries = frappe.get_all(
		"Assignment Log",
		filters={"assigned_user": user, "parenttype": "Enquiry"},
		pluck="parent",
		ignore_permissions=True
	)

	return assigned_enquiries


@frappe.whitelist()
def assign_enquiry(name, assign_user, priority="Medium", description=None):
	"""Assign enquiry to a user"""
	from frappe.utils import now_datetime

	# Get user from User Configuration
	user_config = frappe.db.get_value("User Configuration", assign_user, "user")
	if not user_config:
		frappe.throw(f"User not found for: {assign_user}")

	doc = frappe.get_doc("Enquiry", name)

	# Add entry to Assignment Log child table
	doc.append("table_xlzm", {
		"assigned_user": user_config,
		"assigned_on": now_datetime(),
		"assignment_status": "Assigned",
		"assignment_description": description or ""
	})

	# Update current_owner
	doc.current_owner = user_config

	doc.save(ignore_permissions=True)

	frappe.msgprint(f"Enquiry assigned to {user_config}", alert=True)

	return {"success": True, "assigned_user": user_config}


@frappe.whitelist()
def reassign_enquiry_direct(doctype, name, target_user, description=None):
	"""Reassign enquiry to a target user and reopen."""
	doc = frappe.get_doc(doctype, name)

	# Log Entry
	row = doc.append("table_xlzm", {})
	row.assignment_description = description or ""
	row.assignment_status = "Reassigned"
	row.assigned_on = frappe.utils.now_datetime()
	row.assigned_user = target_user

	doc.save(ignore_permissions=True)

	# Ownership + State
	doc.db_set("current_owner", target_user, update_modified=False)
	doc.db_set("workflow_state", "Open", update_modified=True)
	doc.db_set("status", "Open", update_modified=True)

	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def mark_unclear_direct(doctype, name, reason, current_owner):
	"""Mark enquiry as Unclear and assign back to creator."""
	doc = frappe.get_doc(doctype, name)

	# Reason
	doc.db_set(
		"doubts__clarification_needed",
		reason,
		update_modified=False
	)

	# Log Entry
	row = doc.append("table_xlzm", {})
	row.assignment_description = reason
	row.assignment_status = "Unclear"
	row.assigned_on = frappe.utils.now_datetime()
	row.assigned_user = current_owner

	doc.save(ignore_permissions=True)

	# Ownership + State
	doc.db_set("current_owner", current_owner, update_modified=False)
	doc.db_set("workflow_state", "Unclear", update_modified=True)
	doc.db_set("status", "Unclear", update_modified=True)

	frappe.db.commit()
	return {"success": True}
