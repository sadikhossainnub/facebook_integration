frappe.pages['facebook-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Facebook Dashboard',
		single_column: true
	});

	frappe.facebook_dashboard = new FacebookDashboard(page);
}

class FacebookDashboard {
	constructor(page) {
		this.page = page;
		this.make();
	}

	make() {
		this.page.main.html(`
			<div class="facebook-dashboard">
				<div class="row">
					<div class="col-md-3">
						<div class="card text-center">
							<div class="card-body">
								<h2 class="text-primary" id="total-leads">0</h2>
								<p>Total Leads</p>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card text-center">
							<div class="card-body">
								<h2 class="text-success" id="total-messages">0</h2>
								<p>Messages</p>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card text-center">
							<div class="card-body">
								<h2 class="text-warning" id="total-orders">0</h2>
								<p>Shop Orders</p>
							</div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="card text-center">
							<div class="card-body">
								<h2 class="text-info" id="total-spend">$0</h2>
								<p>Ad Spend</p>
							</div>
						</div>
					</div>
				</div>
				<div class="row mt-4">
					<div class="col-md-6">
						<div class="card">
							<div class="card-header">Leads Trend</div>
							<div class="card-body">
								<canvas id="leads-chart"></canvas>
							</div>
						</div>
					</div>
					<div class="col-md-6">
						<div class="card">
							<div class="card-header">Campaign Performance</div>
							<div class="card-body">
								<canvas id="campaign-chart"></canvas>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		this.load_data();
	}

	load_data() {
		frappe.call({
			method: 'facebook_integration.api.dashboard.get_dashboard_data',
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					this.update_stats(r.message.stats);
					this.render_charts(r.message.charts);
				}
			}
		});
	}

	update_stats(stats) {
		$('#total-leads').text(stats.total_leads);
		$('#total-messages').text(stats.total_messages);
		$('#total-orders').text(stats.total_orders);
		$('#total-spend').text('$' + stats.total_spend.toFixed(2));
	}

	render_charts(charts) {
		// Simple chart rendering - would use Chart.js in production
		console.log('Charts data:', charts);
	}
}