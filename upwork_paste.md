# Compact paste for Upwork Portfolio Item form
#
# This is a tightened ~2000-char version designed for the actual Upwork
# portfolio-item description text field. The longer marketing copy lives
# in upwork_description.md.
#
# Copy everything between the BEGIN/END markers — Upwork supports basic
# markdown (bold, italics, lists, line breaks) in portfolio descriptions.

# ----- BEGIN COPY HERE -----

🏡 **Casa Verde Realty — WhatsApp AI Lead Bot**

A production-ready WhatsApp Business AI assistant that auto-replies to inbound real-estate leads in **under 30 seconds**, qualifies them through a bilingual (EN/ES) conversation, scores them **HOT / WARM / COLD** with an LA-tuned rubric, and drops the lead into Google Sheets + Slack.

🌐 **Live:** https://casa-verde-bot.onrender.com
📦 **Source:** https://github.com/KirillHat/casa-verde-bot

**What it does**
• Auto-detects Spanish vs English and mirrors the prospect
• Qualifies via natural chat: intent → budget → neighborhood → timeline → financing → contact
• Records leads only when complete (Claude `record_lead` tool enforces qualification flow)
• Pushes leads to Google Sheets + Slack alerts to the on-call agent
• Handles edge cases: out-of-budget, casual browsers, hostile/spam, off-topic

**Projected impact for a similar agency**
• Median first-response: 4h → <30s
• Weekend coverage: 25% → 100%
• Leads pre-qualified by AI: 0% → ~80%
• International TZ capture: +180%
• Recovered upcoming sales/mo: ~$2.4M
• Commission recovery/mo: ~$72k

**Tech stack**
Python 3.11 · FastAPI · Anthropic Claude (Sonnet 4.6, prompt caching + tool use) · Twilio WhatsApp · Google Sheets · Slack Block Kit · SQLAlchemy 2 + SQLite · Docker · Render · GitHub Actions CI (py 3.10/3.11/3.12) · 26 pytest tests, 79% coverage

**What's included**
• Production FastAPI app (~2 000 LoC), structured logs, signed Twilio webhook validation, async background processing — acks Twilio in <100 ms
• Deterministic scoring rubric (pure Python, env-tunable)
• Multi-stage Dockerfile (~120 MB image), `render.yaml`, CI matrix
• Step-by-step setup docs (Twilio sandbox 5 min, Google Sheets 5 min)
• Architecture doc with Mermaid sequence diagram
• Brand identity (logo + hero), 4 portfolio screenshots, demo GIF
• Demo seed script — populate your sheet with 28 realistic leads in one command

**Adaptable in 1–2 days** to: yoga studios, solar installers, dental, online schools, travel, B2B SaaS — swap the prompt + scoring rubric, update CRM connector. HubSpot, Pipedrive, Salesforce, Airtable all supported.

**Pricing**
• Vertical adaptation (prompt + scoring + 1 CRM): **$1,500–$2,500** · 2–4 days
• Full integration (CRM + calendar + Slack + branding): **$3,000–$5,000** · 1 week
• White-label / multi-tenant: **$7,000–$15,000** · 2–3 weeks

**Send me a message with:**
1. Your industry
2. Approximate weekly inbound volume
3. Your current CRM
4. Languages you serve

I'll reply within 24 hours with a fixed-price quote + a sample qualifier prompt tailored to your vertical so you can see the tone before committing.

# ----- END COPY -----
