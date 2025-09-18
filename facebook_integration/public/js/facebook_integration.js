// Facebook Integration JavaScript utilities

frappe.provide('facebook_integration');

facebook_integration = {
    // Utility functions for Facebook integration
    
    show_facebook_dialog: function(title, content, callback) {
        let dialog = new frappe.ui.Dialog({
            title: title,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'content',
                    options: content
                }
            ],
            primary_action_label: 'OK',
            primary_action: function() {
                if (callback) callback();
                dialog.hide();
            }
        });
        dialog.show();
    },
    
    format_facebook_timestamp: function(timestamp) {
        if (!timestamp) return 'Never';
        return frappe.datetime.prettyDate(timestamp);
    },
    
    copy_to_clipboard: function(text, message) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                frappe.show_alert({
                    message: message || 'Copied to clipboard!',
                    indicator: 'green'
                });
            });
        } else {
            // Fallback for older browsers
            let textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            frappe.show_alert({
                message: message || 'Copied to clipboard!',
                indicator: 'green'
            });
        }
    },
    
    refresh_facebook_data: function() {
        // Refresh Facebook data across the app
        if (cur_page && cur_page.facebook_dashboard) {
            cur_page.facebook_dashboard.load_stats();
            cur_page.facebook_dashboard.load_recent_data();
        }
    }
};

// Add Facebook-specific list view enhancements
frappe.listview_settings['Facebook Message Log'] = {
    add_fields: ['direction', 'status', 'sender_name'],
    get_indicator: function(doc) {
        if (doc.direction === 'incoming') {
            return [__('Incoming'), 'blue', 'direction,=,incoming'];
        } else {
            return [__('Outgoing'), 'green', 'direction,=,outgoing'];
        }
    }
};

frappe.listview_settings['Facebook Lead Log'] = {
    add_fields: ['synced', 'erpnext_lead'],
    get_indicator: function(doc) {
        if (doc.synced) {
            return [__('Mapped'), 'green', 'synced,=,1'];
        } else {
            return [__('Unmapped'), 'orange', 'synced,=,0'];
        }
    }
};

// Add custom buttons to Facebook Settings
frappe.ui.form.on('Facebook Settings', {
    refresh: function(frm) {
        if (frm.doc.enabled) {
            frm.add_custom_button(__('Test Connection'), function() {
                frappe.call({
                    method: 'facebook_integration.api.dashboard.test_connection',
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: __('Connection Test'),
                                message: r.message.message,
                                indicator: 'green'
                            });
                        } else {
                            frappe.msgprint({
                                title: __('Connection Test Failed'),
                                message: r.message ? r.message.message : 'Unknown error',
                                indicator: 'red'
                            });
                        }
                    }
                });
            });
            
            frm.add_custom_button(__('Sync Now'), function() {
                frappe.call({
                    method: 'facebook_integration.api.insights.sync_campaign_insights',
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: 'Sync completed successfully!',
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
        
        if (!frm.doc.webhook_url && frm.doc.page_id) {
            frm.add_custom_button(__('Generate Webhook URL'), function() {
                let site_url = frappe.utils.get_url();
                let webhook_url = site_url + '/api/method/facebook_integration.api.webhook';
                frm.set_value('webhook_url', webhook_url);
                facebook_integration.copy_to_clipboard(webhook_url, 'Webhook URL copied to clipboard!');
            });
        }
    }
});