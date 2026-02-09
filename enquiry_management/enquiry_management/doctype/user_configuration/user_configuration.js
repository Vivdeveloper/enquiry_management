// Copyright (c) 2026, Vivek Choudhary and contributors
// For license information, please see license.txt

frappe.ui.form.on("User Configuration", {
	refresh: function (frm) {
		set_segment_query(frm);
		set_sub_segment_query(frm);
		apply_role_visibility_uc(frm);
	},
	segments_add: function (frm) {
		set_segment_query(frm);
		set_sub_segment_query(frm);
	},
	user: function (frm) {
		apply_role_visibility_uc(frm);
	}
});

function set_segment_query(frm) {
	const segment_query = function () {
		return {
			filters: {
				parent_segment: "All Segment"
			}
		};
	};

	if (frm.fields_dict.segments && frm.fields_dict.segments.grid) {
		frm.fields_dict.segments.grid.get_field("segment").get_query = segment_query;
	} else {
		frm.set_query("segment", "segments", segment_query);
	}
}

function set_sub_segment_query(frm) {
	const sub_segment_query = function () {
		const parents = (frm.doc.segments || [])
			.map((row) => row.segment)
			.filter((v) => !!v);

		if (!parents.length) {
			return { filters: { name: ["in", ["__none__"]] } };
		}

		return {
			filters: {
				parent_segment: ["in", parents]
			}
		};
	};

	if (frm.fields_dict.sub_segments && frm.fields_dict.sub_segments.grid) {
		frm.fields_dict.sub_segments.grid.get_field("sub_segment").get_query =
			sub_segment_query;
	} else {
		frm.set_query("sub_segment", "sub_segments", sub_segment_query);
	}
}

function apply_role_visibility_uc(frm) {
	if (!frm.doc.user) {
		frm.set_df_property("segments", "hidden", 0);
		frm.set_df_property("sub_segments", "hidden", 0);
		return;
	}

	frappe.call({
		method:
			"enquiry_management.enquiry_management.doctype.user_configuration.user_configuration.get_user_roles",
		args: {
			user: frm.doc.user
		},
		callback: function (r) {
			const roles = r.message || [];
			const is_system_manager = roles.includes("System Manager");
			const is_normal = roles.includes("Normal");

			if (!is_system_manager && is_normal) {
				frm.clear_table("segments");
				frm.clear_table("sub_segments");
				frm.refresh_field("segments");
				frm.refresh_field("sub_segments");
				frm.set_df_property("segments", "hidden", 1);
				frm.set_df_property("sub_segments", "hidden", 1);
			} else {
				frm.set_df_property("segments", "hidden", 0);
				frm.set_df_property("sub_segments", "hidden", 0);
			}
		}
	});
}
