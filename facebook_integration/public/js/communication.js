frappe.ui.form.on('Communication', {
    refresh: function(frm) {
        // Add Facebook Messenger reply button for Facebook messages
        if (frm.doc.communication_medium === 'Facebook Messenger' && 
            frm.doc.sent_or_received === 'Received' &&
            frm.doc.reference_doctype === 'Message Received') {
            
            frm.add_custom_button(__('Reply via Facebook'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Send Facebook Reply'),
                    fields: [
                        {
                            label: __('Message'),
                            fieldname: 'message',
                            fieldtype: 'Text',
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Send'),
                    primary_action: function(values) {
                        frappe.call({
                            method: 'facebook_integration.api.messaging.send_reply_from_communication',
                            args: {
                                communication_name: frm.doc.name,
                                message_text: values.message
                            },
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    frappe.msgprint(__('Reply sent successfully'));
                                    d.hide();
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint(__('Failed to send reply: ') + (r.message.error || 'Unknown error'));
                                }
                            }
                        });
                    }
                });
                d.show();
            }, __('Actions'));
        }
    }
});