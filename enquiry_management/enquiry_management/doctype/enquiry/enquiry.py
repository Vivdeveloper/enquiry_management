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
	Checks the user's Frappe role:
		- Any role: created_by always visible to the creator
		- Normal role: created_by + segment/sub_segment/org must match
		- Head role: can see all enquiries matching segments/sub_segments/orgs
		- assigned_user and reporting_tos always apply
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return None

	user_roles = frappe.get_roles(user)

	if "System Manager" in user_roles:
		return None

	escaped_user = frappe.db.escape(user)

	conditions = []

	# Any role - user can always see enquiries they created
	created_by_match = f"""
		`tabEnquiry`.`created_by` IN (
			SELECT `name` FROM `tabUser Configuration`
			WHERE `user` = {escaped_user}
		)
	"""
	conditions.append(f"({created_by_match})")

	# Normal role - can see own created enquiries matching segments/sub_segments/orgs
	if "Normal" in user_roles:
		segment_match = f"""
			`tabEnquiry`.`segment` IN (
				SELECT `segment`
				FROM `tabUser Configuration Segment`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
			)
		"""

		sub_segment_match = f"""
			`tabEnquiry`.`sub_segment` IN (
				SELECT `sub_segment`
				FROM `tabUser Configuration Sub Segment`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
			)
		"""

		org_match = f"""
			(
				`tabEnquiry`.`primary_organisation` IN (
					SELECT `primary_organisation`
					FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
				OR `tabEnquiry`.`primary_organisation` IN (
					SELECT `organisation`
					FROM `tabUser Configuration Organisation`
					WHERE `parent` IN (
						SELECT `name` FROM `tabUser Configuration`
						WHERE `user` = {escaped_user}
					)
				)
			)
		"""

		normal_created_by = f"""
			`tabEnquiry`.`created_by` IN (
				SELECT `name` FROM `tabUser Configuration`
				WHERE `user` = {escaped_user}
			)
		"""
		conditions.append(f"({normal_created_by} AND {segment_match})")
		conditions.append(f"({normal_created_by} AND {sub_segment_match})")
		conditions.append(f"({normal_created_by} AND {org_match})")

	# Head role - can see all enquiries matching segments/sub_segments/orgs
	if "Head" in user_roles:
		head_segment_match = f"""
			`tabEnquiry`.`segment` IN (
				SELECT `segment`
				FROM `tabUser Configuration Segment`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
			)
		"""

		head_sub_segment_match = f"""
			`tabEnquiry`.`sub_segment` IN (
				SELECT `sub_segment`
				FROM `tabUser Configuration Sub Segment`
				WHERE `parent` IN (
					SELECT `name` FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
			)
		"""

		head_org_match = f"""
			(
				`tabEnquiry`.`primary_organisation` IN (
					SELECT `primary_organisation`
					FROM `tabUser Configuration`
					WHERE `user` = {escaped_user}
				)
				OR `tabEnquiry`.`primary_organisation` IN (
					SELECT `organisation`
					FROM `tabUser Configuration Organisation`
					WHERE `parent` IN (
						SELECT `name` FROM `tabUser Configuration`
						WHERE `user` = {escaped_user}
					)
				)
			)
		"""

		conditions.append(f"({head_segment_match} AND {head_org_match})")
		conditions.append(f"({head_sub_segment_match} AND {head_org_match})")
		conditions.append(f"({head_org_match})")

	# Assigned user - always applies
	is_assigned = f"""
		`tabEnquiry`.`name` IN (
			SELECT `parent`
			FROM `tabAssignment Log`
			WHERE `assigned_user` = {escaped_user}
			AND `parenttype` = 'Enquiry'
		)
	"""
	conditions.append(f"({is_assigned})")

	# Reporting tos - current user can see all data from users who report to them
	reporting_tos_match = f"""
		`tabEnquiry`.`created_by` IN (
			SELECT uc.`name`
			FROM `tabUser Configuration` uc
			WHERE uc.`name` IN (
				SELECT `parent`
				FROM `tabUser Configuration Reporting To`
				WHERE `reporting_to` = {escaped_user}
			)
		)
	"""
	conditions.append(f"({reporting_tos_match})")

	return f"({' OR '.join(conditions)})"


@frappe.whitelist()
def get_permission_info():
	"""Get permission info for the current user"""
	user = frappe.session.user
	permissions = []

	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return {"user": user, "roles": ["Administrator"], "permissions": ["Full Access"]}

	# Check User Configuration
	user_config = frappe.db.get_value(
		"User Configuration",
		{"user": user},
		["name", "primary_organisation"],
		as_dict=True
	)

	if not user_config:
		permissions.append("No User Configuration found - limited access")
		return {"user": user, "roles": [], "permissions": permissions}

	user_roles = frappe.get_roles(user)

	# Collect active permission roles
	active_roles = []
	if "Head" in user_roles:
		active_roles.append("Head")
	if "Normal" in user_roles:
		active_roles.append("Normal")

	# Get user configuration details
	segments = frappe.get_all(
		"User Configuration Segment",
		filters={"parent": user_config.name},
		pluck="segment",
		ignore_permissions=True
	)
	sub_segments = frappe.get_all(
		"User Configuration Sub Segment",
		filters={"parent": user_config.name},
		pluck="sub_segment",
		ignore_permissions=True
	)
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

	# Build simple permission summary
	permissions.append("Your Created Enquiries: Always visible")

	if segments:
		permissions.append(f"Segments: {', '.join(segments)}")
	if sub_segments:
		permissions.append(f"Sub Segments: {', '.join(sub_segments)}")
	if orgs:
		permissions.append(f"Organisations: {', '.join(orgs)}")

	# Assigned enquiries
	assigned_count = frappe.db.count(
		"Assignment Log",
		{"assigned_user": user, "parenttype": "Enquiry"}
	)
	if assigned_count:
		permissions.append(f"Assigned to You: {assigned_count}")

	# Reporting users
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
		permissions.append(f"Team: {', '.join(user_list)}")

	return {"user": user, "roles": active_roles, "permissions": permissions}


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
def mark_unclear(doctype, name, reason, current_owner):
	"""Mark enquiry as Unclear and assign back to creator."""
	doc = frappe.get_doc(doctype, name)

	# Reason
	doc.db_set("doubts__clarification_needed", reason, update_modified=False)

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


@frappe.whitelist()
def reassign_enquiry(doctype, name, target_user, current_owner=None, description=None):
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
