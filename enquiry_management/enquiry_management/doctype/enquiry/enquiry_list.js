frappe.listview_settings['Enquiry'] = {
	onload: function(listview) {
		// Add Check Permissions button
		listview.page.add_inner_button(__('Check Permissions'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_permission_info',
				callback: function(r) {
					if (r.message) {
						let content = `<div style="padding: 10px;">
							<p><strong>User:</strong> ${r.message.user}</p>
							<hr>
							<p><strong>Active Permission Rules:</strong></p>
							<ul style="margin-left: 20px;">
								${r.message.permissions.map(p => `<li>${p}</li>`).join('')}
							</ul>
						</div>`;

						frappe.msgprint({
							title: __('Permission Check'),
							indicator: 'blue',
							message: content
						});
					}
				}
			});
		});

		// Add Filter buttons
		listview.page.add_inner_button(__('My Enquiries'), function() {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, 'created_by', '=', frappe.session.user]]);
			listview.refresh();
		}, __('Filters'));

		listview.page.add_inner_button(__('Assigned to Me'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_assigned_enquiries',
				callback: function(r) {
					if (r.message && r.message.length > 0) {
						listview.filter_area.clear();
						listview.filter_area.add([[listview.doctype, 'name', 'in', r.message]]);
						listview.refresh();
					} else {
						frappe.msgprint(__('No enquiries assigned to you'));
					}
				}
			});
		}, __('Filters'));

		// Filter by My Segments
		listview.page.add_inner_button(__('My Segments'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_user_filter_options',
				callback: function(r) {
					if (r.message && r.message.segments && r.message.segments.length > 0) {
						listview.filter_area.clear();
						listview.filter_area.add([[listview.doctype, 'segment', 'in', r.message.segments]]);
						listview.refresh();
					} else {
						frappe.msgprint(__('No segments configured for you'));
					}
				}
			});
		}, __('Filters'));

		// Filter by My Sub Segments
		listview.page.add_inner_button(__('My Sub Segments'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_user_filter_options',
				callback: function(r) {
					if (r.message && r.message.sub_segments && r.message.sub_segments.length > 0) {
						listview.filter_area.clear();
						listview.filter_area.add([[listview.doctype, 'sub_segment', 'in', r.message.sub_segments]]);
						listview.refresh();
					} else {
						frappe.msgprint(__('No sub segments configured for you'));
					}
				}
			});
		}, __('Filters'));

		// Filter by My Organisations
		listview.page.add_inner_button(__('My Organisations'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_user_filter_options',
				callback: function(r) {
					if (r.message && r.message.organisations && r.message.organisations.length > 0) {
						listview.filter_area.clear();
						listview.filter_area.add([[listview.doctype, 'primary_organisation', 'in', r.message.organisations]]);
						listview.refresh();
					} else {
						frappe.msgprint(__('No organisations configured for you'));
					}
				}
			});
		}, __('Filters'));

		// Filter by Team (Reporting To Me)
		listview.page.add_inner_button(__('My Team'), function() {
			frappe.call({
				method: 'enquiry_management.enquiry_management.doctype.enquiry.enquiry.get_user_filter_options',
				callback: function(r) {
					if (r.message && r.message.reporting_users && r.message.reporting_users.length > 0) {
						listview.filter_area.clear();
						listview.filter_area.add([[listview.doctype, 'created_by', 'in', r.message.reporting_users]]);
						listview.refresh();
					} else {
						frappe.msgprint(__('No team members reporting to you'));
					}
				}
			});
		}, __('Filters'));

		// Clear Filters
		listview.page.add_inner_button(__('Clear Filters'), function() {
			listview.filter_area.clear();
			listview.refresh();
		}, __('Filters'));
	}
};
