"""Conversation orchestrator — wires together Claude, scoring, and CRM/Slack."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import claude_client, scoring, sheets_client, slack_client
from app.storage.models import Conversation, Lead, Message

log = structlog.get_logger()

# Hard cap on history sent back to Claude. The conversation table grows
# unbounded over time; we only need the most recent N turns to maintain
# coherent state, and clipping protects token spend.
_HISTORY_LIMIT = 30


async def handle_inbound(
    session: AsyncSession,
    *,
    phone: str,
    body: str,
) -> str:
    """Process one inbound WhatsApp message; return the reply text."""
    conv = await _get_or_create_conversation(session, phone)
    history = await _load_history(session, conv.id, limit=_HISTORY_LIMIT)

    session.add(Message(conversation_id=conv.id, role="user", content=body))

    reply = await claude_client.chat(history, body)

    session.add(Message(conversation_id=conv.id, role="assistant", content=reply.text))
    await session.flush()

    if reply.lead_data:
        await _record_lead(session, conv, phone, reply.lead_data)

    return reply.text


async def _get_or_create_conversation(session: AsyncSession, phone: str) -> Conversation:
    result = await session.execute(select(Conversation).where(Conversation.phone_number == phone))
    conv = result.scalar_one_or_none()
    if conv is None:
        conv = Conversation(phone_number=phone)
        session.add(conv)
        await session.flush()
    return conv


async def _load_history(session: AsyncSession, conv_id: int, *, limit: int) -> list[dict[str, str]]:
    result = await session.execute(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at.asc())
    )
    msgs = list(result.scalars().all())[-limit:]
    return [{"role": m.role, "content": m.content} for m in msgs]


async def _record_lead(
    session: AsyncSession,
    conv: Conversation,
    phone: str,
    data: dict[str, Any],
) -> None:
    facts = scoring.LeadFacts(
        intent=data["intent"],
        budget_max=int(data.get("budget_max") or 0),
        timeline_months=int(data.get("timeline_months") or 12),
        financing=data.get("financing"),
    )
    label, value = scoring.score_lead(facts)

    lead = Lead(
        conversation_id=conv.id,
        phone=phone,
        name=data.get("name", ""),
        email=data.get("email"),
        intent=data["intent"],
        budget_min=data.get("budget_min"),
        budget_max=facts.budget_max,
        neighborhoods=data.get("neighborhoods", []),
        bedrooms=data.get("bedrooms"),
        timeline_months=facts.timeline_months,
        financing=data.get("financing"),
        must_haves=data.get("must_haves", []),
        language=data.get("language", "en"),
        summary=data.get("summary", ""),
        score=label,
        score_value=value,
    )
    session.add(lead)
    conv.state = "qualified"
    conv.language = data.get("language", conv.language)

    log.info("lead.qualified", phone=phone, score=label, score_value=value, name=lead.name)

    enriched = {**data, "phone": phone}

    # Sheets / Slack failures must never block the WhatsApp reply
    try:
        await sheets_client.append_lead(enriched, label, value)
    except Exception as exc:  # pragma: no cover
        log.error("sheets.append_failed", error=str(exc))
    try:
        await slack_client.notify_lead(enriched, label, value)
    except Exception as exc:  # pragma: no cover
        log.error("slack.notify_failed", error=str(exc))
