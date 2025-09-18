frappe.pages['facebook'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Facebook Integration',
		single_column: true
	});
	
	// Add custom CSS
	$(`<style>
		.facebook-dashboard .card {
			border: none;
			box-shadow: 0 2px 4px rgba(0,0,0,0.1);
			margin-bottom: 20px;
		}
		.facebook-dashboard .stat-card {
			padding: 20px;
			text-align: center;
			border-radius: 8px;
			color: white;
		}
		.facebook-dashboard .stat-card h3 {
			margin: 0;
			font-size: 2rem;
			font-weight: bold;
		}
		.facebook-dashboard .stat-card p {
			margin: 5px 0 0 0;
			opacity: 0.9;
		}
		.facebook-dashboard .btn-facebook {
			background-color: #1877f2;
			border-color: #1877f2;
			color: white;
		}
		.facebook-dashboard .btn-facebook:hover {
			background-color: #166fe5;
			border-color: #166fe5;
		}
	</style>`).appendTo('head');
	
	page.facebook_dashboard = new FacebookDashboard(page);
};

class FacebookDashboard {
	constructor(page) {
		this.page = page;
		this.setup_dashboard();
	}
	
	setup_dashboard() {
		this.page.main.addClass('facebook-dashboard');
		this.load_settings();
		this.render_dashboard();
	}
	
	load_settings() {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Facebook Settings'
			},
			callback: (r) => {
				this.settings = r.message || {};
				this.render_dashboard();
			}
		});
	}
	
	render_dashboard() {
		const html = this.get_dashboard_html();
		this.page.main.html(html);
		this.bind_events();
		this.load_stats();
		this.load_recent_data();
	}
	
	get_dashboard_html() {
		return `
			<div class="row">
				<div class="col-md-12">
					<div class="page-header d-flex justify-content-between align-items-center">
						<h2><i class="fab fa-facebook-square text-primary"></i> Facebook Integration Dashboard</h2>
						<div>
							${this.settings.enabled ? 
								'<button class="btn btn-success btn-sm" id="sync-now"><i class="fa fa-sync"></i> Sync Now</button>' : 
								'<button class="btn btn-primary" onclick="frappe.set_route(\'Form\', \'Facebook Settings\')">Setup Integration</button>'
							}
						</div>
					</div>
				</div>
			</div>
			
			<!-- Statistics Cards -->
			<div class="row" id="stats-row">
				<div class="col-md-3">
					<div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
						<h3 id="total-messages">-</h3>
						<p>Total Messages</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
						<h3 id="total-leads">-</h3>
						<p>Total Leads</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
						<h3 id="unmapped-leads">-</h3>
						<p>Unmapped Leads</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
						<h3 id="today-messages">-</h3>
						<p>Today's Messages</p>
					</div>
				</div>
			</div>
			
			<div class="row">
				<!-- Settings Card -->
				<div class="col-md-6">
					<div class="card">
						<div class="card-header d-flex justify-content-between align-items-center">
							<h5><i class="fa fa-cog"></i> Configuration</h5>
							<span class="badge badge-${this.settings.enabled ? 'success' : 'secondary'}">
								${this.settings.enabled ? 'Active' : 'Inactive'}
							</span>
						</div>
						<div class="card-body">
							${this.get_settings_html()}
						</div>
					</div>
				</div>
				
				<!-- Quick Actions -->
				<div class="col-md-6">
					<div class="card">
						<div class="card-header">
							<h5><i class="fa fa-bolt"></i> Quick Actions</h5>
						</div>
						<div class="card-body">
							<div class="row">
								<div class="col-md-6 mb-2">
									<button class="btn btn-outline-primary btn-sm btn-block" onclick="frappe.set_route('List', 'Facebook Message Log')">
										<i class="fa fa-comments"></i> Messages
									</button>
								</div>
								<div class="col-md-6 mb-2">
									<button class="btn btn-outline-success btn-sm btn-block" onclick="frappe.set_route('List', 'Facebook Lead Log')">
										<i class="fa fa-users"></i> Leads
									</button>
								</div>
								<div class="col-md-6 mb-2">
									<button class="btn btn-outline-info btn-sm btn-block" onclick="frappe.set_route('List', 'Facebook Campaign Metric')">
										<i class="fa fa-chart-line"></i> Metrics
									</button>
								</div>
								<div class="col-md-6 mb-2">
									<button class="btn btn-facebook btn-sm btn-block" id="pull-leads">
										<i class="fa fa-download"></i> Pull Leads
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			
			<div class="row">
				<!-- Recent Messages -->
				<div class="col-md-8">
					<div class="card">
						<div class="card-header d-flex justify-content-between align-items-center">
							<h5><i class="fa fa-comments"></i> Recent Messages</h5>
							<button class="btn btn-sm btn-outline-primary" id="refresh-messages">
								<i class="fa fa-refresh"></i> Refresh
							</button>
						</div>
						<div class="card-body" id="recent-messages">
							<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading...</div>
						</div>
					</div>
				</div>
				
				<!-- Unmapped Leads -->
				<div class="col-md-4">
					<div class="card">
						<div class="card-header">
							<h5><i class="fa fa-user-plus"></i> Unmapped Leads</h5>
						</div>
						<div class="card-body" id="unmapped-leads-list">
							<div class="text-center"><i class="fa fa-spinner fa-spin"></i> Loading...</div>
						</div>
					</div>
				</div>
			</div>
		`;
	}
	
	get_settings_html() {
		if (!this.settings.page_id) {
			return `
				<div class="text-center py-3">
					<i class="fa fa-exclamation-triangle fa-2x text-warning mb-2"></i>
					<p>Facebook integration not configured</p>
					<button class="btn btn-primary" onclick="frappe.set_route('Form', 'Facebook Settings')">
						Setup Integration
					</button>
				</div>
			`;
		}
		
		return `
			<div class="row">
				<div class="col-md-12">
					<p><strong>Page:</strong> ${this.settings.page_name || 'Not set'}</p>
					<p><strong>Page ID:</strong> <code>${this.settings.page_id}</code></p>
					<p><strong>Last Synced:</strong> ${this.settings.last_synced ? frappe.datetime.prettyDate(this.settings.last_synced) : 'Never'}</p>
					<button class="btn btn-primary btn-sm" onclick="frappe.set_route('Form', 'Facebook Settings')">
						<i class="fa fa-edit"></i> Configure
					</button>
				</div>
			</div>
		`;
	}
	
	bind_events() {
		// Sync now button
		$('#sync-now').on('click', () => {
			this.sync_now();
		});
		
		// Pull leads button
		$('#pull-leads').on('click', () => {
			this.pull_leads();
		});
		
		// Refresh messages
		$('#refresh-messages').on('click', () => {
			this.load_recent_data();
		});
	}
	
	load_stats() {
		frappe.call({
			method: 'facebook_integration.www.facebook_integration.get_facebook_stats',
			callback: (r) => {
				if (r.message) {
					const stats = r.message;
					$('#total-messages').text(stats.total_messages || 0);
					$('#total-leads').text(stats.total_leads || 0);
					$('#unmapped-leads').text(stats.unmapped_leads || 0);
					$('#today-messages').text(stats.today_messages || 0);
				}
			}
		});
	}
	
	load_recent_data() {
		// Load recent messages
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Facebook Message Log',
				fields: ['name', 'sender_name', 'content', 'direction', 'status', 'creation'],
				order_by: 'creation desc',
				limit_page_length: 5
			},
			callback: (r) => {
				this.render_recent_messages(r.message || []);
			}
		});
		
		// Load unmapped leads
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Facebook Lead Log',
				filters: {'synced': 0},
				fields: ['name', 'fb_leadgen_id', 'creation'],
				order_by: 'creation desc',
				limit_page_length: 5
			},
			callback: (r) => {
				this.render_unmapped_leads(r.message || []);
			}
		});
	}
	
	render_recent_messages(messages) {
		if (!messages.length) {
			$('#recent-messages').html('<div class="text-center text-muted">No messages found</div>');
			return;
		}
		
		let html = '<div class="list-group list-group-flush">';
		messages.forEach(msg => {
			const badge = msg.direction === 'incoming' ? 
				'<span class="badge badge-info">In</span>' : 
				'<span class="badge badge-success">Out</span>';
			
			html += `
				<div class="list-group-item">
					<div class="d-flex justify-content-between align-items-start">
						<div class="flex-grow-1">
							<h6 class="mb-1">${msg.sender_name || 'Unknown'} ${badge}</h6>
							<p class="mb-1 text-muted small">${(msg.content || '').substring(0, 60)}${msg.content && msg.content.length > 60 ? '...' : ''}</p>
						</div>
						<small class="text-muted">${frappe.datetime.prettyDate(msg.creation)}</small>
					</div>
				</div>
			`;
		});
		html += '</div>';
		
		$('#recent-messages').html(html);
	}
	
	render_unmapped_leads(leads) {
		if (!leads.length) {
			$('#unmapped-leads-list').html('<div class="text-center text-muted">No unmapped leads</div>');
			return;
		}
		
		let html = '<div class="list-group list-group-flush">';
		leads.forEach(lead => {
			html += `
				<div class="list-group-item d-flex justify-content-between align-items-center">
					<div>
						<h6 class="mb-1">${lead.fb_leadgen_id}</h6>
						<small class="text-muted">${frappe.datetime.prettyDate(lead.creation)}</small>
					</div>
					<button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form', 'Facebook Lead Log', '${lead.name}')">
						Map
					</button>
				</div>
			`;
		});
		html += '</div>';
		
		$('#unmapped-leads-list').html(html);
	}
	
	sync_now() {
		frappe.call({
			method: 'facebook_integration.api.insights.sync_campaign_insights',
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Sync completed successfully!', indicator: 'green'});
					this.load_stats();
					this.load_recent_data();
				} else {
					frappe.show_alert({message: 'Sync failed!', indicator: 'red'});
				}
			}
		});
	}
	
	pull_leads() {
		frappe.call({
			method: 'facebook_integration.api.leads.fetch_leads',
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Leads pulled successfully!', indicator: 'green'});
					this.load_stats();
					this.load_recent_data();
				} else {
					frappe.show_alert({message: 'Failed to pull leads!', indicator: 'red'});
				}
			}
		});
	}
}