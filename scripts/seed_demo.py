"""Seed the local SQLite DB with three example conversations.

Useful for sanity-checking that the model + scoring + persistence all
work together without touching Twilio. Requires a real ANTHROPIC_API_KEY
in your environment (the conversations actually call Claude).

Sheets and Slack are stubbed out — set SLACK_NOTIFY_ENABLED=false and
make GOOGLE_CREDENTIALS_JSON point to a non-existent file if you don't
want CRM side-effects.

    python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import os

# Sensible defaults so the script runs in a half-configured dev env
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACdemo")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "demo")
os.environ.setdefault("GOOGLE_SHEETS_ID", "demo")
os.environ.setdefault("SLACK_NOTIFY_ENABLED", "false")
os.environ.setdefault("DEBUG_SKIP_TWILIO_SIGNATURE", "true")

from app.services import conversation  # noqa: E402
from app.storage.db import init_db, session_scope  # noqa: E402

DEMO_MESSAGES: list[tuple[str, str]] = [
    (
        "+14155550100",
        "Hola, busco un depto 2BR en West Hollywood, max $1.5M, "
        "financiamiento internacional, mudanza en 3 meses. Soy Carlos.",
    ),
    (
        "+14155550101",
        "Hi, relocating from NYC for a Google job, need a 2BR rental in Venice "
        "or Silver Lake, budget $5k/mo, need it for Sept 1. I'm Sarah.",
    ),
    (
        "+14155550102",
        "yo just looking around, what's a decent area in LA for $600k?",
    ),
]


async def main() -> None:
    await init_db()
    for phone, body in DEMO_MESSAGES:
        async with session_scope() as session:
            print(f"\n→ {phone}: {body!r}")
            reply = await conversation.handle_inbound(session, phone=phone, body=body)
            print(f"← {reply}")


if __name__ == "__main__":
    asyncio.run(main())
