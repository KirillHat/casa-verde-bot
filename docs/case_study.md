# Case study — Casa Verde Realty

> **Westside boutique. Worldwide buyers.**
>
> Casa Verde Realty is a fictional but realistic boutique real-estate
> agency in Santa Monica, used here to demonstrate a production WhatsApp
> AI lead qualifier. Every name, number and metric below is an
> illustrative example of how this system would perform for a similar
> agency — the codebase is real and ready to deploy.

## The agency

| | |
|---|---|
| **Name** | Casa Verde Realty |
| **Founded** | 2018 by Diana Acosta (formerly with Compass) |
| **Office** | Santa Monica, CA · `+1 (310) 555-0142` |
| **Team** | 8 licensed agents + 1 office manager (Maria) |
| **Specialty** | Westside LA + Eastside trendy (Silver Lake, Echo Park) |
| **Price band** | $850k–$10M sales · $2.5k–$15k/mo rentals |
| **Buyer mix** | Local HNW 40% · International LATAM/Asia 30% · Out-of-state movers 20% · Entertainment 10% |

## The problem

Casa Verde is bombarded with **150+ inbound WhatsApp messages per week**, mostly from:

- **Zillow / Redfin** "contact agent" forms that route to WhatsApp
- **International buyers** from Mexico, Brazil, China and Korea — WhatsApp is their default channel; email is dead
- **Instagram ad** click-throughs from "$2M Venice flip" reels
- **Past-client referrals** — friend of a friend, fast-moving

The agents are on showings 9 AM–7 PM and at open houses every weekend. **Median first-response time is 4 hours**, and on weekends often >12 hours. By the time an agent replies, the international buyer has DM'd Compass, Coldwell Banker and Sotheby's — Casa Verde loses the lead before the conversation ever starts.

Maria, the office manager, tried to triage messages in real time, but she's not licensed and can't qualify for budget or financing — and she's still one human in one timezone.

## The solution

A WhatsApp Business AI assistant ("Sofia") that:

1. **Auto-replies in <30 seconds** to every inbound message, 24/7
2. **Qualifies the lead** through a natural conversation: intent → budget → neighborhoods → bedrooms → timeline → financing → contact
3. **Mirrors the user's language** — switches between English and Spanish automatically (critical for international + LA Latino buyers)
4. **Scores the lead** using an LA-tuned rubric (HOT / WARM / COLD)
5. **Pushes the lead** into a Google Sheet that the team already lives in
6. **Pings the on-call agent** in Slack so a human follows up while the lead is still warm
7. **Never makes up listings** — Sofia qualifies, then hands the relationship to a licensed human agent

## The conversation

Three real-feeling examples — the bot you can run from this repo handles all three identically.

### Conversation A — Mexican buyer (Spanish)

> **Sofia (auto-reply, 30s after first ping):**
> ¡Hola! Soy Sofia, asistente de Casa Verde Realty 🏡 ¿Buscas comprar o rentar?
>
> **Carlos:** Comprar. Una casa 3BR en Santa Monica, hasta $2.5M.
>
> **Sofia:** ¡Perfecto, Westside es lo nuestro! ¿Cuándo te quieres mudar?
>
> **Carlos:** En 4 meses, vengo desde Ciudad de México.
>
> **Sofia:** Buenísimo. ¿Cómo lo financias — al contado, jumbo loan, o foreign-national?
>
> **Carlos:** Foreign national, ya tengo pre-aprobación.
>
> **Sofia:** Excelente. ¿Cómo te llamas para que un agente te contacte?
>
> **Carlos:** Carlos Reyes, mi email es carlos@example.com.
>
> **Sofia:** ¡Listo, Carlos! Diana o Tomás te escribirán en menos de una hora con opciones. ✨

→ **Lead score:** 🔥 HOT (95 / 100) — high budget + foreign-national pre-approval + 4-month timeline

### Conversation B — NYC tech mover (English)

> **Sarah:** Hi, relocating from NYC for a Google job, need a 2BR rental in Venice or Silver Lake, budget $5k/mo, need it for Sept 1.
>
> **Sofia:** Welcome to LA, Sarah! 🏡 Sept 1 is doable in both. Furnished or unfurnished? Pet-friendly important?
>
> **Sarah:** Unfurnished, no pets. Walk to coffee shops > parking.
>
> **Sofia:** Got it — Venice walk-to-coffee-shop is exactly what Tomás specializes in. He'll ping you within the hour. ✨

→ **Lead score:** 🟡 WARM (75 / 100) — premium rental, urgent timeline

### Conversation C — Casual cold lead (English)

> **Anonymous:** yo just looking around, what's a decent area in LA for $600k?
>
> **Sofia:** Honestly, $600k in our coverage area (Westside + Eastside trendy) is mostly small studios — most of our 1BRs start around $850k. Want me to flag you for new listings under $1M as they pop up?
>
> **Anonymous:** sure
>
> **Sofia:** Cool — what's your name and email so an agent can keep you in the loop?

→ **Lead score:** 🔵 COLD (30 / 100) — budget below market, no firm timeline. Still recorded for nurture campaign.

## The results (illustrative — what a similar agency could expect)

| Metric | Before | After |
|---|---|---|
| Median first-response time | **4 h** | **<30 s** |
| Weekend response coverage | ~25% | **100%** |
| Leads qualified before agent touch | 0% | **~80%** |
| International leads captured (Asia / LATAM TZ) | low | **+180%** |
| Time agents spend on first-touch qualification | ~10 h/wk | **~1 h/wk** |
| Recovered upcoming sales (first month) | — | **~$2.4 M** |
| Estimated commission recovery (~3% buyer side) | — | **~$72 k / month** |

## Why this is hard (so it's worth building)

A "WhatsApp bot that uses ChatGPT" is a meme — most are useless because they:

1. **Don't qualify** — they small-talk forever and never push toward a decision
2. **Don't score** — every lead looks the same to the agent
3. **Don't speak the buyer's language** — fail open to English or use bad translation
4. **Block the webhook** — call the LLM synchronously and time out at 15 s, losing the message
5. **Have no observability** — when leads disappear, nobody knows why

This bot solves all five:

- Claude is given a **strict qualification flow with a `record_lead` tool** — no aimless chatting; the LLM only finishes a turn by calling the tool once it has enough info
- A **deterministic LA-tuned scoring rubric** ranks every lead the moment it's recorded (no LLM-as-judge variance)
- **Bilingual by design** — the system prompt instructs language mirroring, demonstrated end-to-end
- The webhook **acks Twilio in <100 ms** and processes in a background task — Twilio never times out
- Structured logs (structlog), Sentry hooks, signed-webhook validation and a CI test suite mean failures are visible

## Adapting this for a different niche

The architecture is generic — the only domain-specific pieces are:

- [`app/prompts/qualifier_realestate.md`](../app/prompts/qualifier_realestate.md) — the conversational rules
- [`app/services/scoring.py`](../app/services/scoring.py) — the HOT/WARM/COLD rubric

To repurpose this for a yoga studio, dental clinic, solar installer, online school, or travel agency, swap those two files and update the Google Sheet headers in `app/services/sheets_client.py`. **Whole adaptation: ~2 hours.**

That portability is the actual product — *not* "a real-estate bot."
