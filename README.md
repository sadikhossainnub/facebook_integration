# Facebook ⇄ ERPNext Integration

A comprehensive Frappe/ERPNext app that integrates Facebook Page Messenger, Lead Ads, and Campaign Insights with ERPNext.

## Features

- **Facebook Messenger Integration**: Capture and respond to Facebook Page messages
- **Lead Ads Integration**: Automatically import Facebook Lead Ads into ERPNext
- **Campaign Insights**: Pull Facebook Ads campaign metrics and performance data
- **Lead Mapping**: Map Facebook leads to ERPNext Leads, Contacts, or Customers
- **Webhook Support**: Real-time message and lead capture via Facebook webhooks
- **Scheduled Sync**: Automated daily sync of insights and periodic lead fetching

## Installation

1. Install the app:
```bash
bench get-app facebook_integration
bench install-app facebook_integration
```

2. Configure Facebook App:
   - Create a Facebook App at https://developers.facebook.com
   - Add Messenger and Lead Ads products
   - Generate Page Access Token
   - Set up webhook subscriptions

3. Configure in ERPNext:
   - Go to Facebook Settings
   - Enter your Facebook App credentials
   - Set webhook URL in Facebook App settings
   - Enable the integration

## Setup Guide

### Facebook App Configuration

1. **Create Facebook App**:
   - Go to Facebook Developers Console
   - Create new app for "Business"
   - Add Messenger and Lead Ads products

2. **Generate Access Token**:
   - Go to Messenger > Settings
   - Generate Page Access Token for your page
   - Copy the token to ERPNext Facebook Settings

3. **Setup Webhooks**:
   - Add webhook URL: `https://yoursite.com/api/method/facebook_integration.api.webhook`
   - Subscribe to: `messages`, `messaging_postbacks`, `leadgen`
   - Use verify token from ERPNext settings

### ERPNext Configuration

1. **Facebook Settings**:
   - Page ID: Your Facebook Page ID
   - App ID: Facebook App ID
   - App Secret: Facebook App Secret
   - Access Token: Page Access Token
   - Verify Token: Custom verification token

2. **Permissions**:
   - Assign "Facebook Admin" role for full access
   - Assign "Facebook Agent" role for message handling

## API Endpoints

- `POST /api/method/facebook_integration.api.webhook` - Facebook webhook
- `POST /api/method/facebook_integration.api.send_message` - Send message
- `GET /api/method/facebook_integration.api.get_messages` - Get messages
- `POST /api/method/facebook_integration.api.map_lead` - Map Facebook lead
- `POST /api/method/facebook_integration.api.pull_insights` - Pull campaign insights

## Scheduled Tasks

- **Daily**: Sync Facebook campaign insights
- **Every 5 minutes**: Fetch pending leads
- **Weekly**: Cleanup old logs

## Doctypes

- **Facebook Settings**: Configuration settings
- **Facebook Message Log**: Message history
- **Facebook Lead Log**: Lead capture log
- **Facebook Campaign Metric**: Campaign performance data

## License

MIT