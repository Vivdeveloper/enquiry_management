// Copyright (c) 2026, Vivek Choudhary and contributors
// For license information, please see license.txt

frappe.ui.form.on('Enquiry', {
	refresh: function(frm) {
		set_customer_filter_enq(frm);
		set_segment_filters(frm);

		// Execute only for new documents
		if (frm.is_new() && !frm.doc.current_owner) {
			// Owner is the creator at creation time
			frm.set_value('current_owner', frm.doc.owner);
		}

		// If submitted/cancelled, make form read-only
		if (frm.doc.docstatus !== 0) {
			(frm.fields || []).forEach((f) => {
				if (f && f.df && f.df.fieldname) {
					frm.set_df_property(f.df.fieldname, 'read_only', 1);
				}
			});
		}

		// Read-only for non-owners/non-admins
		let can_edit = false;

		if (frm.doc.current_owner === frappe.session.user) {
			can_edit = true;
		}

		if (frappe.user.has_role('System Manager') || frappe.session.user === 'Administrator') {
			can_edit = true;
		}

		if (!can_edit && !frm.is_new()) {
			(frm.fields || []).forEach((f) => {
				if (f && f.df && f.df.fieldname) {
					frm.set_df_property(f.df.fieldname, 'read_only', 1);
				}
			});
			frm.set_intro(__('You can only view this enquiry. Only the Current Owner, Assign Team or System Manager can edit.'), 'yellow');
		}

		render_enquiry_type_radio(frm);
		render_project_type_radio(frm);

		// Show Assign To button for Open enquiries where current user is owner
		if (frm.doc.status === "Open" && frm.doc.current_owner === frappe.session.user) {
			frm.add_custom_button('Assign To', function() {
				show_assign_popup(frm);
			}).addClass('btn-primary');
		}

		const is_current_owner = frm.doc.current_owner === frappe.session.user;
		const is_creator = frm.doc.created_by === frappe.session.user;

		// MARK AS UNCLEAR — ONLY FOR ASSIGNED USER (NOT CREATOR)
		if (
			frm.doc.docstatus === 0 &&
			frm.doc.status === "Open" &&
			is_current_owner &&
			!is_creator
		) {
			frm.add_custom_button("Mark as Unclear", () => {
				frappe.prompt(
					[
						{
							label: "Doubts / Clarification",
							fieldname: "reason",
							fieldtype: "Small Text",
							reqd: 1
						}
					],
					function(values) {
						frappe.call({
							method: "enquiry_management.enquiry_management.doctype.enquiry.enquiry.mark_unclear",
							args: {
								doctype: frm.doc.doctype,
								name: frm.doc.name,
								reason: values.reason,
								current_owner: frm.doc.created_by
							},
							callback() {
								frm.reload_doc();
							}
						});
					},
					"Clarification Required",
					"Confirm"
				);
			}).addClass("btn-warning");
		} else {
			frm.remove_custom_button("Mark as Unclear");
		}

		// REASSIGN BUTTON — ONLY FOR CURRENT OWNER IN UNCLEAR
		if (
			frm.doc.docstatus === 0 &&
			frm.doc.workflow_state === "Unclear" &&
			is_current_owner
		) {
			frm.add_custom_button("Reassign", () => {
				setTimeout(() => {
					frappe.prompt(
						[
							{
								label: "Reassign Description",
								fieldname: "desc",
								fieldtype: "Small Text",
								reqd: 1
							}
						],
						function(values) {
							let rows = frm.doc.table_xlzm || [];
							let target_user =
								rows.length > 1
									? rows[rows.length - 2].assigned_user
									: null;

							if (!target_user) {
								frappe.msgprint("Target user not found");
								return;
							}

							frappe.call({
								method: "enquiry_management.enquiry_management.doctype.enquiry.enquiry.reassign_enquiry",
								args: {
									doctype: frm.doc.doctype,
									name: frm.doc.name,
									target_user: target_user,
									current_owner: target_user,
									description: values.desc
								},
								callback() {
									frm.reload_doc();
									frappe.show_alert({
										message: "Reassigned and reopened",
										indicator: "green"
									});
								}
							});
						},
						"Reassign Enquiry",
						"Confirm"
					);
				}, 0);
			}).addClass("btn-warning");
		} else {
			frm.remove_custom_button("Reassign");
		}

		// Hide Cancel button for Open status
		try {
			if (frm.doc.status === "Open") {
				if (frm.page.remove_menu_item) {
					frm.page.remove_menu_item(__('Cancel'));
				}
				if (frm.page.btn_primary) {
					frm.page.btn_primary.hide();
				}
				frm.page.wrapper
					.find('button.btn.btn-secondary.btn-default.btn-sm')
					.filter(function() {
						return $(this).text().trim() === __('Cancel');
					})
					.hide();
			}
		} catch (e) {
			console.error("Error hiding cancel button:", e);
		}
	},

	customer_type: function(frm) {
		frm.set_value('customer_name', null);
		frm.set_value('end_user_name', null);
		set_customer_filter_enq(frm);
	},

	customer_name: function(frm) {
		if (frm.doc.customer_type === "End User" && frm.doc.customer_name) {
			frm.set_value('end_user_name', frm.doc.customer_name);
		}
	},

	segment: function(frm) {
		frm.set_value('sub_segment', null);
		frm.set_value('sub_sub_segment', null);
		set_segment_filters(frm);
	},

	sub_segment: function(frm) {
		frm.set_value('sub_sub_segment', null);
		set_segment_filters(frm);
	}
});

function set_customer_filter_enq(frm) {
	frm.set_query('customer_name', function() {
		if (!frm.doc.customer_type) {
			return {};
		}
		return {
			filters: {
				type_customer: frm.doc.customer_type
			}
		};
	});
}

function set_segment_filters(frm) {
	// Segment = Level 2 (children of root: All Segment)
	frm.set_query('segment', function() {
		return {
			filters: {
				parent_segment: "All Segment"
			}
		};
	});

	// Sub Segment = Level 3 (children of selected Segment)
	frm.set_query('sub_segment', function() {
		if (!frm.doc.segment) {
			return { filters: { name: ['in', ['__none__']] } };
		}
		return {
			filters: {
				parent_segment: frm.doc.segment
			}
		};
	});

	// Sub Sub Segment = Level 4 (children of selected Sub Segment)
	frm.set_query('sub_sub_segment', function() {
		if (!frm.doc.sub_segment) {
			return { filters: { name: ['in', ['__none__']] } };
		}
		return {
			filters: {
				parent_segment: frm.doc.sub_segment
			}
		};
	});
}

function render_enquiry_type_radio(frm) {
	const field = frm.get_field('enquiry_type_radio');
	if (!field || !field.$wrapper) {
		return;
	}

	const options = ['Firm', 'Budgetory', 'Idea', 'Tender'];
	const current = frm.doc.enquiry_type || '';
	const is_locked = frm.doc.docstatus !== 0;
	const wrapper = field.$wrapper;

	wrapper.empty().append(`
		<div class="form-group">
			<label class="control-label" style="margin-bottom: 8px;">
				Enquiry Type <span class="reqd">*</span>
			</label>
			<div class="radio-group" style="display: flex; flex-direction: column; gap: 10px;">
				${options.map((opt) => `
					<label class="radio" style="display: flex; align-items: center; gap: 10px; margin: 0;">
						<input type="radio" name="enquiry_type_radio" value="${opt}" ${current === opt ? 'checked' : ''} ${is_locked ? 'disabled' : ''}>
						${opt}
					</label>
				`).join('')}
			</div>
		</div>
	`);

	wrapper.off('change.enquiry_type_radio').on('change.enquiry_type_radio', 'input[name="enquiry_type_radio"]', function() {
		frm.set_value('enquiry_type', this.value);
	});
}

function render_project_type_radio(frm) {
	const field = frm.get_field('project_type_radio');
	if (!field || !field.$wrapper) {
		return;
	}

	const options = ['New', 'Expansion', 'Retrofit', 'Spares'];
	const current = frm.doc.project_type || '';
	const is_locked = frm.doc.docstatus !== 0;
	const wrapper = field.$wrapper;

	wrapper.empty().append(`
		<div class="form-group">
			<label class="control-label" style="margin-bottom: 8px;">
				Project Type <span class="reqd">*</span>
			</label>
			<div class="radio-group" style="display: flex; flex-direction: column; gap: 10px;">
				${options.map((opt) => `
					<label class="radio" style="display: flex; align-items: center; gap: 10px; margin: 0;">
						<input type="radio" name="project_type_radio" value="${opt}" ${current === opt ? 'checked' : ''} ${is_locked ? 'disabled' : ''}>
						${opt}
					</label>
				`).join('')}
			</div>
		</div>
	`);

	wrapper.off('change.project_type_radio').on('change.project_type_radio', 'input[name="project_type_radio"]', function() {
		frm.set_value('project_type', this.value);
	});
}

function show_assign_popup(frm) {
	const dialog = frappe.prompt([
        {
			fieldname: 'department',
			fieldtype: 'Link',
			label: 'Department',
			options: 'Department',
			only_select: 1,
			reqd: 1
		},
		{
			fieldtype: 'Column Break'
		},
		{
			fieldname: 'assign_user',
			fieldtype: 'Link',
			label: 'Assign To User',
			options: 'User Configuration',
			only_select: 1,
			reqd: 1
		},
		{
			fieldname: 'assign_to_me',
			fieldtype: 'Check',
			label: 'Assign to me',
			default: 0,
			onchange: function() {
				const assign_to_me = dialog.get_value('assign_to_me');
				if (assign_to_me) {
					frappe.db.get_value(
						'User Configuration',
						{ user: frappe.session.user },
						'name'
					).then((r) => {
						const user_config = r && r.message && r.message.name;
						if (user_config) {
							dialog.set_value('assign_user', user_config);
						} else {
							dialog.set_value('assign_to_me', 0);
							frappe.msgprint(__('No User Configuration found for your user.'));
						}
					});
				} else {
					dialog.set_value('assign_user', null);
				}
			}
		},
		{
			fieldtype: 'Section Break',
		},
		{
			fieldname: 'priority',
			fieldtype: 'Select',
			label: 'Priority',
			options: 'Low\nMedium\nHigh',
			default: 'Medium'
		},
		{
			fieldname: 'description',
			fieldtype: 'Small Text',
			label: 'Description',
			reqd: 1
		}
	],
	function(values) {
		frappe.call({
			method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.assign_enquiry',
			args: {
				name: frm.doc.name,
				assign_user: values.assign_user,
				priority: values.priority,
				description: values.description
			},
			callback: function(r) {
				if (r.message) {
					frm.reload_doc();
				}
			}
		});
	},
	'Assign Enquiry',
	'Assign'
	);

	dialog.fields_dict.assign_user.get_query = function() {
		const department = dialog.get_value('department');
		if (department) {
			return {
				filters: {
					department: department
				}
			};
		}
		return {};
	};
}
