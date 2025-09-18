frappe.ui.form.on('Facebook Settings', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.enabled) {
			frm.add_custom_button(__('Test Connection'), function() {
				test_facebook_connection(frm);
			});
			
			frm.add_custom_button(__('Refresh Token'), function() {
				refresh_facebook_token(frm);
			});
			
			frm.add_custom_button(__('Pull Insights'), function() {
				pull_facebook_insights(frm);
			});
		}
		
		// Show webhook URL
		if (frm.doc.webhook_url) {
			frm.set_df_property('webhook_url', 'description', 
				'Copy this URL to your Facebook App webhook settings');
		}
	},
	
	enabled: function(frm) {
		if (frm.doc.enabled) {
			// Generate webhook URL when enabled
			if (!frm.doc.webhook_url) {
				frm.set_value('webhook_url', 
					window.location.origin + '/api/method/facebook_integration.api.webhook');
			}
		}
	}
});

function test_facebook_connection(frm) {
	frappe.call({
		method: 'facebook_integration.api.insights.get_campaign_metrics',
		args: {},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__('Facebook connection is working!'));
			} else {
				frappe.msgprint(__('Facebook connection failed. Please check your settings.'));
			}
		}
	});
}

function refresh_facebook_token(frm) {
	frappe.call({
		method: 'facebook_integration.api.insights.refresh_token',
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__('Token refreshed successfully'));
				frm.reload_doc();
			} else {
				frappe.msgprint(__('Failed to refresh token: ') + (r.message.error || 'Unknown error'));
			}
		}
	});
}

function pull_facebook_insights(frm) {
	frappe.call({
		method: 'facebook_integration.api.insights.pull_insights',
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.msgprint(__('Insights pulled successfully: ') + r.message.insights_count + __(' records'));
				frm.reload_doc();
			} else {
				frappe.msgprint(__('Failed to pull insights'));
			}
		}
	});
}