# Architecture

## High-level flow

```mermaid
sequenceDiagram
    participant U as Prospect (WhatsApp)
    participant T as Twilio
    participant A as Bot (FastAPI)
    participant C as Claude API
    participant DB as SQLite
    participant G as Google Sheets
    participant S as Slack

    U->>T: "Hola, busco un depto en Venice"
    T->>A: POST /webhooks/whatsapp (signed)
    A->>T: 200 OK · <Response/> · <100ms
    Note over A: webhook returns immediately;<br/>processing continues in background

    A->>DB: load conversation history
    A->>C: messages.create(history + new msg + tools)
    C-->>A: text reply (and possibly tool_use record_lead)
    A->>DB: save user + assistant messages

    alt Lead qualified by Claude
        A->>A: scoring.score_lead() → HOT/WARM/COLD
        A->>DB: save Lead row
        A->>G: append_row()
        A->>S: post lead notification
    end

    A->>T: messages.create(reply text)
    T->>U: WhatsApp reply
```

## Components

### `app/main.py`
FastAPI app factory. On startup it configures `structlog`, optionally initializes Sentry (`SENTRY_DSN` env var), creates the SQLite schema if missing, and ensures the Google Sheet has its header row.

### `app/webhooks/whatsapp.py`
The Twilio webhook handler:

1. **Validates `X-Twilio-Signature`** using Twilio's `RequestValidator` against `TWILIO_AUTH_TOKEN`. Skippable in dev with `DEBUG_SKIP_TWILIO_SIGNATURE=true`.
2. **Returns empty TwiML 200 immediately** so Twilio doesn't time out (the LLM call may take 2–6 s).
3. **Schedules `_process_and_reply`** as a `BackgroundTask`.

Also exposes `GET /healthz` for uptime monitoring and Render's health checks.

### `app/services/conversation.py`
Orchestrates one inbound message:

- Loads or creates a `Conversation` row (one per phone number, unique index)
- Loads the last 30 messages as Claude history (cap protects token spend on long-running prospects)
- Calls `claude_client.chat()` — gets back text + (optionally) `lead_data`
- Persists the user + assistant messages
- If `lead_data` present: scores it, persists a `Lead` row, fires Sheets + Slack
- Sheets / Slack failures are logged but never block the WhatsApp reply

### `app/services/claude_client.py`
Wraps the Anthropic Python SDK:

- Loads the system prompt from [`app/prompts/qualifier_realestate.md`](../app/prompts/qualifier_realestate.md)
- Sends the system prompt with `cache_control: {"type": "ephemeral"}` — the first call is full price, subsequent calls in the same 5-minute window pay roughly **10× less** for system tokens
- Defines the single `record_lead` tool with strict required fields
- Returns a `ClaudeReply(text, lead_data)` — `lead_data` is `None` until Claude calls the tool

### `app/services/scoring.py`
Pure-Python lead scoring. No LLM, no network, no surprises.

| Intent | Signal | Weight |
|---|---|---|
| **Buy** | Budget ≥ $1.5 M | +40 |
| Buy | Budget $0.8–1.5 M | +25 |
| Buy | Cash | +30 |
| Buy | Jumbo / foreign-national | +25 |
| Buy | Conventional | +15 |
| Buy | Timeline ≤ 2 months | +30 |
| Buy | Timeline ≤ 6 months | +20 |
| **Rent** | Budget ≥ $5 k/mo | +40 |
| Rent | Budget $3–5 k/mo | +25 |
| Rent | Timeline ≤ 1 month | +35 |
| Rent | (inherent shorter cycle) | +20 |

Default thresholds: **HOT ≥ 80 · WARM ≥ 50 · COLD < 50**. Tunable per-call and via env vars.

### `app/services/sheets_client.py`
`gspread` wrapped in `asyncio.to_thread`. One `append_lead()` call → one new row, columns matching the agreed [headers](google_sheets_setup.md#header-reference). `ensure_headers()` runs at startup to create the header row idempotently.

### `app/services/slack_client.py`
Async `httpx.AsyncClient` POST to a Slack incoming-webhook URL. Uses Block Kit for a rich card with header, four field columns (intent, budget, timeline, phone), summary blockquote, and a context line. Respects `SLACK_NOTIFY_MIN_SCORE` so cold leads don't ping the channel.

### `app/storage/`
SQLAlchemy 2.0 async with `aiosqlite`. Three tables:

- **`conversations`** — one per phone number, tracks language and state
- **`messages`** — full transcript, used to rebuild Claude's history
- **`leads`** — one per qualified prospect, with score and full structured fields

SQLite is intentionally chosen — for one agency's 100–500 leads/week it's plenty, with zero ops overhead. Swap `DATABASE_URL` to Postgres if you outgrow it.

## Why a background task instead of a synchronous reply?

WhatsApp via Twilio expects the webhook to respond in <15 seconds. Claude calls take 2–6 seconds, plus ~1 second each for Sheets and Slack. A synchronous flow risks timing out under load and dropping messages.

By acking immediately and processing in the background, we:

- Never lose a Twilio retry-storm
- Get clean separation between HTTP I/O and LLM/CRM I/O
- Can scale background workers independently (e.g. swap `BackgroundTasks` for a Celery worker if needed)

The trade-off: errors during background processing surface in logs / Sentry, not in the HTTP response. That's the right trade-off for this use case — the prospect just sees that the bot didn't reply, and the agency sees the error in observability.

## Why SQLite over Postgres?

- Casa Verde does ~150 leads/week. SQLite handles that with one finger.
- Single-file DB → trivially backed up (`cp leads.db leads.db.bak`).
- Render / Fly free tier doesn't include managed Postgres.
- `DATABASE_URL` is the only thing to change if you grow into Postgres.

## Why FastAPI?

- Async-native, fits Twilio's ack-fast pattern.
- Pydantic v2 models give us typed Twilio form validation for free.
- Uvicorn + Gunicorn workers scale linearly.
- The whole app is ~700 LoC — one engineer can read it on a Tuesday afternoon.

## Why Claude (vs GPT-4 / Gemini)?

- **Tool use** is rock-solid — when the prompt says "call `record_lead` when ready", Claude does
- **Prompt caching** on the system prompt is ~10× cheaper after the first hit, which compounds in a chatty WhatsApp use case
- **Long context** means we can append the full transcript on every turn instead of doing summarization gymnastics
- The Sonnet tier (`claude-sonnet-4-6`) is the sweet spot of quality vs cost for short, conversational turns

The codebase is provider-agnostic at the service boundary — `claude_client.py` is the only file you'd swap to use a different LLM.

## What's intentionally NOT in v1

- **Outbound campaigns** — no "blast 200 contacts" feature. WhatsApp template messaging requires Meta approval and is a separate product.
- **Voice / images** — Twilio supports MMS in WhatsApp, but qualifying off images needs vision and a different pipeline.
- **Scheduled re-engagement** — "haven't heard from you in 3 days, still looking?" — straightforward to add via APScheduler, deferred to v1.1.
- **Multi-tenant** — one bot, one agency. Tenancy would be three lines (`tenant_id` column + sub-router) but is out of scope for the demo.
