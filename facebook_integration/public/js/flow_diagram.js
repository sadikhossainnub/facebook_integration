// Flow diagram interactive functionality
frappe.ready(function() {
    // Add real-time status updates
    if (window.location.pathname.includes('flow_diagram')) {
        loadFlowStatus();
        setInterval(loadFlowStatus, 30000); // Update every 30 seconds
    }
});

function loadFlowStatus() {
    frappe.call({
        method: 'facebook_integration.api.flow_monitor.get_flow_status',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                updateFlowStatus(r.message.data);
            }
        }
    });
}

function updateFlowStatus(data) {
    // Update webhook status indicators
    const webhookSection = document.querySelector('.webhook-status');
    if (webhookSection) {
        webhookSection.innerHTML = `
            <h4>🔗 Webhook Status</h4>
            <div class="status-grid">
                ${data.webhook_status.map(account => `
                    <div class="status-item ${account.webhook_active ? 'active' : 'inactive'}">
                        <strong>${account.account_name}</strong>
                        <span>${account.webhook_active ? '✅ Active' : '⚠️ Inactive'}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Update activity counters
    const activitySection = document.querySelector('.activity-status');
    if (activitySection) {
        activitySection.innerHTML = `
            <h4>📊 Today's Activity</h4>
            <div class="activity-grid">
                <div class="activity-item">
                    <span class="count">${data.recent_activity.leads_today}</span>
                    <span class="label">Leads</span>
                </div>
                <div class="activity-item">
                    <span class="count">${data.recent_activity.messages_today}</span>
                    <span class="label">Messages</span>
                </div>
                <div class="activity-item">
                    <span class="count">${data.recent_activity.orders_today}</span>
                    <span class="label">Orders</span>
                </div>
            </div>
        `;
    }
}