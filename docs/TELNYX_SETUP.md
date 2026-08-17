# Telnyx Setup Guide

This guide walks you through getting your SMS number set up with Telnyx and connecting it to the CRM.

## Prerequisites

1. **Telnyx account** — sign up at https://telnyx.com
2. **Production HTTPS URL** — Telnyx webhooks require HTTPS (use ngrok for development)
3. **API key** — for sending SMS programmatically

## Step 1: Create Telnyx Account & Get Keys

1. Sign up at https://telnyx.com/sign-up
2. Log in to the Telnyx Dashboard: https://portal.telnyx.com
3. Navigate to **Account > API Keys** (or **Settings > Auth** in older UI)
4. Create a new API key (V2) if you don't have one
5. Copy the key to your `.env` as `TELNYX_API_KEY`

Example `.env` entry:
```
TELNYX_API_KEY=KEY12345abcdef
```

## Step 2: Get Your Account Public Key

1. In the Telnyx Dashboard, go to **Account > Public Key**
2. Your public key (base64-encoded) is displayed there
3. Copy it to your `.env` as `TELNYX_PUBLIC_KEY`

Example:
```
TELNYX_PUBLIC_KEY=LS0tLS1CRUdJTiBQVUJMSUMgS0VZLi4u
```

## Step 3: Create a Messaging Profile

1. Go to **Messaging > Messaging Profiles** in the Telnyx Dashboard
2. Click **Create Messaging Profile**
3. Name it (e.g., "Appointment Setter") and click **Create**
4. Copy the Profile ID to your `.env` as `TELNYX_MESSAGING_PROFILE_ID`

Example:
```
TELNYX_MESSAGING_PROFILE_ID=12345678-abcd-efgh-ijkl-mnopqrstuvwx
```

## Step 4: Request a 10DLC Number

10DLC (10-digit long code) numbers are required for business SMS in the US.

1. Go to **Messaging > Phone Numbers** in Telnyx
2. Click **Buy Numbers** or **Request Phone Numbers**
3. Filter by:
   - Country: **United States**
   - Number Type: **10DLC**
   - Features: **SMS**
4. Select your desired number and click **Buy**
5. Assign it to the Messaging Profile you created in Step 3

Once assigned, copy your number to `.env` as `TELNYX_FROM_NUMBER`:
```
TELNYX_FROM_NUMBER=+18135550100
```

## Step 5: Register 10DLC Brand & Campaign

10DLC requires brand and campaign registration for compliance.

1. Go to **Messaging > 10DLC Campaigns** in Telnyx Dashboard
2. Click **Create Brand** (if you don't have one)
   - Business name: your insurance agency name
   - Business type: "Insurance"
   - Website: your company website
   - EIN: your tax ID
3. Await brand approval (usually 1-2 hours)
4. Once approved, create a **Campaign**:
   - Brand: select your brand
   - Campaign Name: "Life & Health Insurance Appointments"
   - Use Case: **Customer Care** (not Marketing)
   - Message Frequency: As needed
   - Reference: Your business license or appointment confirmation
5. Copy the Campaign ID (you may need it later for higher volume)

Campaign approval typically takes a few days.

## Step 6: Set Up Webhook URL

The CRM needs a webhook URL to receive inbound SMS and delivery receipts.

### In Development (with ngrok)

1. Start ngrok tunnel to your local server:
   ```bash
   ngrok http 8000
   ```
2. Note the HTTPS URL (e.g., `https://abc123.ngrok.io`)
3. The webhook will be: `https://abc123.ngrok.io/webhooks/telnyx`

### In Production

Use your production domain:
```
https://your-domain.com/webhooks/telnyx
```

## Step 7: Configure Webhook in Telnyx

1. Go to **Messaging > Messaging Profiles** in Telnyx
2. Select your Messaging Profile
3. In **Inbound Settings**, set:
   - **Webhook URL**: `https://<your-url>/webhooks/telnyx`
   - **Send Dlr (Delivery Receipt)**: Enabled
   - **Dlr Fallback URL**: same as above
4. Click **Save**

## Step 8: Fill .env File

Update your `.env` with all the credentials:

```env
# Database (SQLite for dev, Postgres for prod)
DATABASE_URL=sqlite:///./dev.db

# Telnyx SMS
TELNYX_API_KEY=KEY12345abcdef
TELNYX_PUBLIC_KEY=LS0tLS1CRUdJTi...
TELNYX_MESSAGING_PROFILE_ID=12345678-abcd-efgh-ijkl-mnopqrstuvwx
TELNYX_FROM_NUMBER=+18135550100

# LLM (DeepSeek or your preferred OpenAI-compatible API)
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=deepseek-v4-flash

# Booking (Calendly or static link)
BOOKING_PROVIDER=static
STATIC_BOOKING_URL=https://calendly.com/yourname/intro

# Behavior
AUTO_SEND=true                 # false = require approval; true = send automatically
QUIET_HOURS_START=21           # No sends at or after 9pm
QUIET_HOURS_END=9              # No sends before 9am
DRY_RUN=false                  # true = no actual SMS sent; false = live SMS

# Throughput (stay at/under your 10DLC MPS limit)
WORKER_INTERVAL_SECONDS=30
SEND_RATE_PER_MINUTE=60
```

## Step 9: Test the Connection

1. Start the CRM server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Send a test SMS to your Telnyx number from your phone

3. Check the CRM console at `http://localhost:8000`
   - Your phone number should appear as a contact
   - Your message should be in the conversation thread

4. If using `AUTO_SEND=true`, you should see an outbound reply within seconds

5. Check delivery in Telnyx Dashboard → **Messaging > Message Logs**

## Troubleshooting

### No inbound messages received
- **Check webhook URL**: Verify it's HTTPS and accessible
- **Check Telnyx logs**: Go to **Messaging > Message Logs** and look for failed/error status
- **Verify signature**: Make sure `TELNYX_PUBLIC_KEY` is correct (copy again from Dashboard)
- **Test locally**: Use ngrok and test with curl to verify the endpoint

### No outbound SMS sent
- **Check DRY_RUN**: Make sure it's set to `false`
- **Check compliance gates**: Is it within quiet hours? Did contact opt-out?
- **Check Telnyx logs**: Messages might be queued waiting for MPS limits
- **Check API key**: Make sure `TELNYX_API_KEY` is valid

### 10DLC Campaign not approved
- **Check status**: Go to **Messaging > 10DLC Campaigns** and check approval status
- **Provide documentation**: Some brands require business license or registration proof
- **Contact Telnyx support**: They can expedite approval if needed

### Webhook signature verification fails
- **Use correct public key**: Copy from **Account > Public Key** in Dashboard
- **Verify base64**: The key should be base64-encoded
- **Check for whitespace**: Remove any leading/trailing spaces

## Monitoring

Once live, monitor your SMS flow:

1. **Telnyx Dashboard**: Message logs, delivery receipts, campaign status
2. **CRM Console**: `/contacts/metrics` shows sent/delivered/booked
3. **Server logs**: Check for errors in the application output

## Compliance Notes

- **STOP keyword**: Contacts who text "STOP" are automatically opted out
- **Quiet hours**: Messages won't send outside configured hours (default 9am-9pm)
- **Message frequency**: Keep campaigns conversational, not promotional
- **Opt-out**: Always respect customer opt-out requests immediately

## Production Deployment

Before going live:

1. Use a real domain with HTTPS (not ngrok)
2. Switch to Postgres if storing more than a few hundred contacts
3. Set `AUTO_SEND=true` once you trust the agent responses
4. Test the full flow with a few real leads first
5. Monitor delivery rates and response quality
6. Set up error alerting on your server

For Docker deployment, see the main README.md.
