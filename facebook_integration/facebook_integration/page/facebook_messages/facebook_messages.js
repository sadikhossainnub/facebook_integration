frappe.pages['facebook-messages'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Facebook Messages',
		single_column: true
	});

	frappe.facebook_messages = new FacebookMessages(page);
}

class FacebookMessages {
	constructor(page) {
		this.page = page;
		this.make();
	}

	make() {
		this.page.main.html(`
			<div class="facebook-messages">
				<div class="row">
					<div class="col-md-4">
						<div class="card">
							<div class="card-header">
								<select class="form-control" id="account-filter">
									<option value="">All Accounts</option>
								</select>
							</div>
							<div class="card-body" style="height: 500px; overflow-y: auto;">
								<div id="conversations-list"></div>
							</div>
						</div>
					</div>
					<div class="col-md-8">
						<div class="card">
							<div class="card-header">
								<span id="conversation-title">Select a conversation</span>
							</div>
							<div class="card-body" style="height: 400px; overflow-y: auto;">
								<div id="messages-container"></div>
							</div>
							<div class="card-footer">
								<div class="input-group">
									<input type="text" class="form-control" id="message-input" placeholder="Type a message...">
									<div class="input-group-append">
										<button class="btn btn-primary" id="send-btn">Send</button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		this.bind_events();
		this.load_accounts();
		this.load_conversations();
	}

	bind_events() {
		$('#send-btn').click(() => this.send_message());
		$('#message-input').keypress((e) => {
			if (e.which === 13) this.send_message();
		});
		$('#account-filter').change(() => this.load_conversations());
	}

	load_accounts() {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Facebook Account',
				filters: {enabled: 1, enable_messenger: 1},
				fields: ['name', 'account_name']
			},
			callback: (r) => {
				if (r.message) {
					let options = '<option value="">All Accounts</option>';
					r.message.forEach(acc => {
						options += `<option value="${acc.name}">${acc.account_name}</option>`;
					});
					$('#account-filter').html(options);
				}
			}
		});
	}

	load_conversations() {
		const account = $('#account-filter').val();
		frappe.call({
			method: 'facebook_integration.api.messaging.get_messages',
			args: {account_name: account, limit: 50},
			callback: (r) => {
				if (r.message && r.message.success) {
					this.render_conversations(r.message.messages);
				}
			}
		});
	}

	render_conversations(messages) {
		const conversations = {};
		messages.forEach(msg => {
			const key = msg.direction === 'incoming' ? msg.sender_id : msg.recipient_id;
			if (!conversations[key]) {
				conversations[key] = {
					id: key,
					name: msg.sender_name || key,
					last_message: msg.content,
					time: msg.received_at || msg.sent_at
				};
			}
		});

		let html = '';
		Object.values(conversations).forEach(conv => {
			html += `
				<div class="conversation-item p-2 border-bottom" data-id="${conv.id}">
					<strong>${conv.name}</strong>
					<p class="text-muted small">${conv.last_message}</p>
					<small>${conv.time}</small>
				</div>
			`;
		});

		$('#conversations-list').html(html);
		$('.conversation-item').click((e) => {
			const id = $(e.currentTarget).data('id');
			this.load_conversation(id);
		});
	}

	load_conversation(sender_id) {
		const account = $('#account-filter').val();
		frappe.call({
			method: 'facebook_integration.api.messaging.get_conversation',
			args: {sender_id: sender_id, account_name: account},
			callback: (r) => {
				if (r.message && r.message.success) {
					this.render_messages(r.message.messages);
					this.current_sender = sender_id;
					$('#conversation-title').text(`Conversation with ${sender_id}`);
				}
			}
		});
	}

	render_messages(messages) {
		let html = '';
		messages.forEach(msg => {
			const isOutgoing = msg.direction === 'outgoing';
			html += `
				<div class="message ${isOutgoing ? 'outgoing' : 'incoming'} mb-2">
					<div class="p-2 rounded ${isOutgoing ? 'bg-primary text-white ml-auto' : 'bg-light'}" style="max-width: 70%;">
						${msg.content}
						<small class="d-block mt-1">${msg.received_at || msg.sent_at}</small>
					</div>
				</div>
			`;
		});
		$('#messages-container').html(html);
		$('#messages-container').scrollTop($('#messages-container')[0].scrollHeight);
	}

	send_message() {
		const message = $('#message-input').val().trim();
		const account = $('#account-filter').val();
		
		if (!message || !this.current_sender || !account) return;

		frappe.call({
			method: 'facebook_integration.api.messaging.send_message',
			args: {
				account_name: account,
				recipient_id: this.current_sender,
				message_text: message
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					$('#message-input').val('');
					this.load_conversation(this.current_sender);
				}
			}
		});
	}
}