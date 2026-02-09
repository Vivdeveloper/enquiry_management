// Copyright (c) 2026, Vivek Choudhary and contributors
// For license information, please see license.txt

frappe.ui.form.on("User Configuration", {
	refresh: function (frm) {
		set_segment_filters_uc(frm);
	}
});

function set_segment_filters_uc(frm) {
	// Level 2 only in Segments table (children of root)
	const segment_query = function () {
		return {
			filters: {
				parent_segment: ["in", ["Segment", "", null]]
			}
		};
	};

	if (frm.fields_dict.segments && frm.fields_dict.segments.grid) {
		frm.fields_dict.segments.grid.get_field("segment").get_query = segment_query;
	} else {
		frm.set_query("segment", "segments", segment_query);
	}

	// Level 3 only in Sub Segments table, filtered by selected Level 2 segments
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
