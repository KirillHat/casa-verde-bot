# Casa Verde Realty — WhatsApp AI Lead Bot
*(production-ready open-source codebase + full case study)*

**Built for:** *Casa Verde Realty* — a fictional but realistic boutique real-estate agency in Santa Monica, CA, used as a believable case study to demonstrate the system end-to-end.

**Stack:** Python 3.11 · FastAPI · Anthropic Claude (Sonnet 4.6) · Twilio WhatsApp Business API · Google Sheets · Slack · SQLite · Docker · GitHub Actions

**Live demo:** message the Twilio sandbox number on WhatsApp with the join code from the GitHub README — talk to **Sofia** in English or Spanish.

**Code:** <https://github.com/KirillHat/casa-verde-bot>

---

## What it does

A WhatsApp Business assistant that auto-replies to inbound prospect messages in **under 30 seconds**, qualifies them through a natural bilingual conversation (intent → budget → neighborhood → timeline → financing → contact), scores them HOT / WARM / COLD with an LA real-estate-tuned rubric, drops the lead into a Google Sheet your team already uses, and pings the on-call agent in Slack.

## Why it matters (for a similar agency)

| Metric | Before | After |
|---|---|---|
| Median first-response time | 4 h | **<30 s** |
| Weekend response coverage | ~25% | **100%** |
| Leads qualified before human touch | 0% | **~80%** |
| International (Asia / LATAM TZ) capture | low | **+180%** |
| Recovered upcoming sales / month | — | **~$2.4 M** |
| Estimated commission recovery / month | — | **~$72 k** |

## What's in the box

- **Production FastAPI app** (~700 LoC) with structured logging, Sentry hooks, signed Twilio webhook validation, async background processing
- **LA-tuned scoring rubric** in pure Python (testable, tunable)
- **Bilingual prompt** (en / es) with mandatory tool use to enforce qualification flow
- **Google Sheets CRM integration** — service account auth, auto-created header row, idempotent
- **Slack Block Kit notifications** with score-based filtering
- **SQLAlchemy 2 + aiosqlite** for conversation memory across restarts
- **Docker** multi-stage build (~120 MB final image), Docker Compose, **`render.yaml`** for free-tier Render deploy
- **pytest + pytest-asyncio + ruff** with **GitHub Actions CI** (matrix Python 3.10 / 3.11 / 3.12)
- **Step-by-step setup docs** for Twilio Sandbox (5 min) and Google Sheets (5 min)
- **Bonus:** portable to any vertical — yoga studio, solar, dental, travel — by swapping the prompt and scoring file

## What it took

- ~3 days from blank repo to production
- Test suite covers scoring rules, conversation flow with mocked Claude, webhook signature validation, and the no-blocking-on-CRM-failure invariant
- Documented architecture decisions: why background tasks, why SQLite, why deterministic scoring vs LLM-judged

## I can do this for you

If you run a real-estate, dental, fitness, education, travel, solar, or any other lead-driven business with WhatsApp inbound, I can adapt this **in 1–2 days** to your vertical, brand, and CRM (Google Sheets, HubSpot, Pipedrive, Airtable, Salesforce). Drop me a message.
