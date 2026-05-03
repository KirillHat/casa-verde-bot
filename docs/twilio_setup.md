# Twilio WhatsApp — 5-minute setup

This guide gets you a working WhatsApp number you can test the bot with, **without** going through Meta's Business Manager verification (which takes 1–4 weeks). Perfect for portfolio demos and development.

## Step 1 — Create a Twilio account

1. Go to <https://www.twilio.com/try-twilio>
2. Sign up with email + phone verification
3. You get **$15 free trial credit** (~5,000 outbound messages)

## Step 2 — Activate the WhatsApp Sandbox

1. In the Twilio Console, navigate to **Messaging → Try it out → Send a WhatsApp message**
   ([direct link](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn))
2. You'll see a sandbox number like `+1 415 523 8886` and a unique join code, e.g. `join green-rabbit`
3. From your personal WhatsApp, send `join green-rabbit` to that number
4. Twilio replies *"Connected to Sandbox"* — your phone is now in the sandbox

> **Sandbox limitations.** Each user must opt in by sending the join code. The 24-hour conversation window applies — if a user is silent for >24 h, they re-send the join code.

## Step 3 — Grab your credentials

1. Twilio Console → **Account → Account Info**
2. Copy:
   - **Account SID** → `TWILIO_ACCOUNT_SID` in `.env`
   - **Auth Token** → `TWILIO_AUTH_TOKEN` in `.env`
3. The sandbox number is already `+14155238886` — keep `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886`

## Step 4 — Wire up the webhook

Twilio needs a public HTTPS URL to send incoming messages to. Two options:

### Option A — Local development with ngrok

```bash
# Terminal 1
uvicorn app.main:app --reload --port 8000

# Terminal 2
ngrok http 8000
# copy the https://xxxxx.ngrok.io URL
```

### Option B — Production on Render

Push the repo to GitHub, then on Render:

1. New → Web Service → connect repo
2. Render auto-detects [`render.yaml`](../render.yaml)
3. Set the env vars from `.env.example` in the Render dashboard
4. Add `google_credentials.json` as a Secret File mounted at `/etc/secrets/google_credentials.json`
5. Deploy. Public URL is `https://your-service.onrender.com`

### Either way, register the webhook in Twilio:

1. Twilio Console → **Messaging → Try it out → WhatsApp Sandbox Settings**
2. **When a message comes in:** `https://your-public-url/webhooks/whatsapp` (HTTP POST)
3. **Status callback URL:** leave blank (or point to the same `/webhooks/whatsapp` for delivery receipts)
4. Save

## Step 5 — Test it

From your phone WhatsApp, message the sandbox number:

> *"Hi, looking for a 2BR rental in Venice"*

You should see:
1. An AI-generated reply within 5 seconds
2. A row appear in your Google Sheet (once Sofia qualifies you)
3. A Slack notification fire (if `SLACK_WEBHOOK_URL` is set)

Tail the logs to confirm:

```bash
# Local
uvicorn app.main:app --reload | jq .

# Render
render logs -f --service casa-verde-bot
```

You're looking for events like:

```json
{"event": "whatsapp.inbound", "phone": "+14155550100", "body_len": 38}
{"event": "lead.qualified", "phone": "+14155550100", "score": "WARM", "score_value": 65}
```

## Switching to production WhatsApp

When you're ready to use a real WhatsApp Business number (not the sandbox):

1. Apply for a **Twilio Sender** at Console → Senders → WhatsApp senders
2. Submit your business profile to Meta for verification (5–14 days)
3. Once approved, swap `TWILIO_WHATSAPP_FROM` to the new `whatsapp:+...` number
4. **No code changes needed** — the same webhook handler works for sandbox and production

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Webhook never fires | Twilio can't reach your URL | `curl https://your-url/healthz` should return 200 |
| `403 Invalid Twilio signature` | `TWILIO_AUTH_TOKEN` mismatch | Re-copy from Console → Account Info; no trailing whitespace |
| Twilio called but no reply sent | Background task crashed | Check logs for `whatsapp.processing_failed` |
| `Sandbox session expired` (> 24 h) | WhatsApp policy | User re-sends `join <code>` |
| Reply lands but no Sheets row | Service-account email not shared on the sheet | See [google_sheets_setup.md](google_sheets_setup.md#step-3) |
| Reply lands but no Slack ping | `SLACK_NOTIFY_MIN_SCORE` excluded the lead | Drop to `COLD` to confirm wiring, then raise back |
