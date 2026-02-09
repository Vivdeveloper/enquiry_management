// Copyright (c) 2026, Vivek Choudhary and contributors
// For license information, please see license.txt

frappe.ui.form.on("Segment", {
	validate: async function (frm) {
		const depth = await get_segment_depth(frm.doc.parent_segment);
		if (depth === 4 && frm.doc.is_group) {
			frappe.throw("Level 4 cannot be a Group. Set is_group = 0 to create it.");
		}
	},
});

async function get_segment_depth(parent_segment) {
	if (!parent_segment) {
		return 1;
	}

	let depth = 1;
	let parent = parent_segment;
	while (parent) {
		depth += 1;
		const result = await frappe.db.get_value(
			"Segment",
			parent,
			"parent_segment"
		);
		parent = result && result.message && result.message.parent_segment;
	}

	return depth;
}
