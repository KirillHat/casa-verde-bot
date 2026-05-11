# Casa Verde Realty — WhatsApp AI Lead Bot

> A production-ready WhatsApp Business AI assistant that auto-replies to inbound real-estate leads in **under 30 seconds**, qualifies them through a bilingual (EN/ES) conversation, scores them **HOT / WARM / COLD** with an LA-tuned rubric, and drops the lead into **Google Sheets + Slack**.
>
> Built end-to-end. Production-deployed. Adaptable to any niche in 1–2 days.

🌐 **Live:** <https://casa-verde-bot.onrender.com>
📦 **Source:** <https://github.com/KirillHat/casa-verde-bot>
💬 **Try it on WhatsApp:** see the GitHub README for the Twilio sandbox number + join code — chat with **Sofia** in English or Spanish.

> *Casa Verde Realty is a fictional but realistic boutique agency in Santa Monica, used here as a believable end-to-end demo. The codebase is real, the system is deployed, and the architecture transfers directly to any client.*

---

## What it does

- **Auto-detects Spanish vs English** on the first message and mirrors the prospect — switches mid-conversation if they switch
- **Qualifies via natural conversation:** intent → budget → neighborhood → timeline → financing → contact
- **Records leads only when complete.** Claude is given the `record_lead` tool with strict required fields, so the LLM only finishes a turn by calling it once it has enough info — no aimless small talk
- **Scores them deterministically** in pure Python (HOT / WARM / COLD) — no LLM-as-judge variance, fully tunable per niche
- **Pushes the lead** to a Google Sheet your team already uses (auto-creates the header row), and pings the on-call agent in Slack with a Block Kit card
- **Edge-case aware** — out-of-budget, casual browsers, hostile / spam, off-topic, existing-client all handled politely in the prompt

## Projected impact (illustrative — for a similar agency)

> The numbers below are an illustrative projection for a comparable boutique
> agency, based on industry response-time benchmarks. They are not historical
> revenue from Casa Verde (Casa Verde is a fictional demo brand).

| Metric | Before | After |
|---|---|---|
| Median first-response time | 4 h | **<30 s** |
| Weekend response coverage | ~25% | **100%** |
| Leads pre-qualified by AI | 0% | **~80%** |
| International (Asia / LATAM TZ) capture | low | **+180%** |
| Recovered upcoming sales / month (illustrative) | — | **~$2.4 M** |
| Estimated commission recovery / month (illustrative) | — | **~$72 k** |
| Time agents spend on first-touch qualification | ~10 h/wk | **~1 h/wk** |

## Tech stack

`Python 3.11` · `FastAPI` · `Anthropic Claude` (Sonnet 4.6, **prompt caching** + **tool use**) · `Twilio WhatsApp Business API` (signed-webhook validation) · `Google Sheets` (service account) · `Slack Block Kit` · `SQLAlchemy 2.0 async + aiosqlite` · `Docker` (multi-stage, ~120 MB image) · `Render` free-tier deploy via `render.yaml` · `GitHub Actions CI` (matrix Python 3.10 / 3.11 / 3.12) · `ruff` (lint + format) · `pytest + pytest-asyncio` (28 tests, 79% coverage)

## What's in the box

- **Production FastAPI app** (~2 000 LoC) with structured logging (`structlog`), Sentry hooks, signed Twilio webhook validation, async background processing — webhook acks Twilio in <100 ms regardless of LLM latency
- **LA-tuned deterministic scoring rubric** — recognises Casa Verde's premium segment (foreign-national loans, jumbo, cash) and rentals separately; thresholds are env-tunable
- **Bilingual qualifier prompt** with auto-injected current-date header so Claude can compute `timeline_months` correctly
- **Google Sheets CRM integration** — service-account auth, auto-created header row, idempotent
- **Slack Block Kit notifications** with score-based filtering (no ping for cold leads if you don't want)
- **SQLAlchemy 2 async + aiosqlite** — conversation memory survives restarts
- **Multi-stage Dockerfile** (non-root user) + `docker-compose.yml` + `render.yaml` for one-click Render deploy
- **GitHub Actions CI** — pytest matrix across Python 3.10 / 3.11 / 3.12 + ruff lint and format check
- **Step-by-step setup docs** for Twilio Sandbox (5 min) and Google Sheets (5 min)
- **Architecture doc** with Mermaid sequence diagram and component-by-component rationale
- **Brand identity** — logo + hero photo, social-preview banner, 4 portfolio screenshots (HTML + Playwright pipeline so they regenerate from one HTML file)
- **Demo seed script** — one command to populate your Sheet with 28 realistic LA leads for instant portfolio polish

## Adaptable in 1–2 days

The architecture is generic. To repurpose for a different vertical, swap two files:

- `app/prompts/qualifier_realestate.md` — domain context + qualification fields
- `app/services/scoring.py` — your industry's HOT/WARM/COLD rules

Then update the Sheet headers. **Whole adaptation: ~2 hours of focused work.** The portability is the actual product — *not* "a real-estate bot."

Verticals I've planned ports for:

| Vertical | Qualifying fields | Use case |
|---|---|---|
| **Yoga / fitness studios** | experience level, goals, schedule, package | IG ads → DM funnel |
| **Solar installers** | home ownership, monthly bill, roof, address | Google Ads → quote |
| **Dental / medical** | procedure, insurance, urgency, location | Receptionist offload |
| **Online schools / coaching** | language/subject, current level, goal, budget | International TZ capture |
| **Travel / tour operators** | trip type, dates, group size, fitness, budget | 24/7 inquiry handling |
| **B2B SaaS / agencies** | company size, current tools, pain, budget | SDR replacement |

CRM target can be **Google Sheets** (default, free), **HubSpot**, **Pipedrive**, **Salesforce**, **Airtable**, or any combination — each connector is ~50 LoC.

## Pricing & engagement

| Scope | Indicative price | Timeline |
|---|---|---|
| Vertical adaptation (prompt + scoring + 1 CRM) | **$1,500 – $2,500** | 2–4 days |
| Full integration (CRM + calendar + Slack + custom branding) | **$3,000 – $5,000** | 1 week |
| White-label / multi-tenant build (one bot, multiple brands) | **$7,000 – $15,000** | 2–3 weeks |
| WhatsApp Business API (Meta) verification setup | included | + 5–14 days Meta review |

I work fixed-price with milestone deliverables. First call is free and ends with a signed Statement of Work the same day.

## Why this is hard (so you should hire someone who's done it)

A "WhatsApp bot that uses ChatGPT" is a meme — most are useless because they:

1. **Don't qualify** — they small-talk forever and never push toward a decision
2. **Don't score** — every lead looks identical to the agent
3. **Don't speak the buyer's language** — fail open to English or use bad translation
4. **Block the webhook** — call the LLM synchronously, time out at 15 s, drop messages
5. **Have no observability** — when leads disappear, nobody knows why

This bot solves all five. The README explains each architectural decision in plain English — you can read it in 10 minutes and audit my approach before we even talk.

## Want this for your business?

Send me a message with:

1. **Your industry** (e.g. solar in California, online English school, real-estate in Madrid)
2. **Approximate inbound volume** per week (10? 100? 1000?)
3. **Your current CRM** (or "we use Google Sheets")
4. **Languages** you serve

I'll reply within 24 hours with a fixed-price quote and a sample qualifier prompt tailored to your vertical, so you can see the tone before committing.

---

**Code:** <https://github.com/KirillHat/casa-verde-bot>
**Live:** <https://casa-verde-bot.onrender.com>
**License:** MIT (you keep ownership of any adaptation I build for you)
