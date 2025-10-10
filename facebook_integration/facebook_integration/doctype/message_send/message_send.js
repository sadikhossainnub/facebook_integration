frappe.ui.form.on('Message Send', {
	refresh: function(frm) {
		if (frm.doc.status === 'draft' && !frm.doc.__islocal) {
			frm.add_custom_button(__('Send Message'), function() {
				frm.call('send_message').then(() => {
					frm.reload_doc();
				});
			});
		}
	}
});