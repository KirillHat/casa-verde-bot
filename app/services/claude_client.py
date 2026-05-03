"""Anthropic Claude client with prompt caching and tool-use lead recording.

The system prompt lives in ``app/prompts/qualifier_realestate.md`` and is
loaded once at import time. It's sent with ``cache_control: ephemeral`` so
that the system tokens are billed at ~10% on subsequent requests inside
the 5-minute cache window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from anthropic import AsyncAnthropic
from anthropic.types import Message, TextBlock, ToolUseBlock

from app.config import get_settings

_settings = get_settings()
_client = AsyncAnthropic(api_key=_settings.anthropic_api_key.get_secret_value())

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "qualifier_realestate.md"
_SYSTEM_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _build_system_prompt() -> str:
    """Inject today's date so Claude can compute timeline_months correctly.

    Without this, Claude has no way to know what 'September 1' means in
    relative terms — it would guess and inflate or deflate the lead score.
    """
    today = datetime.now(ZoneInfo(_settings.business_timezone))
    header = (
        f"Today is {today.strftime('%A, %B %-d, %Y')} "
        f"({_settings.business_timezone}). When the prospect mentions a "
        f"month or date, compute `timeline_months` as the number of whole "
        f"months from today to that date.\n\n---\n\n"
    )
    return header + _SYSTEM_PROMPT_TEMPLATE


# The single tool Claude is allowed to call. Strict required-fields enforce
# that no half-qualified lead ever reaches the CRM.
RECORD_LEAD_TOOL: dict[str, Any] = {
    "name": "record_lead",
    "description": (
        "Record a qualified prospect in the CRM. Call this AS SOON AS you have: "
        "intent (buy/rent), budget_max, at least one neighborhood, timeline_months, "
        "and the prospect's first name. Do NOT keep asking optional questions once "
        "you have these required fields — better to record an 80%-complete lead "
        "than lose the prospect."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Prospect's first name (minimum)."},
            "email": {"type": "string", "description": "Optional email address."},
            "intent": {"type": "string", "enum": ["buy", "rent"]},
            "budget_min": {
                "type": "integer",
                "description": "Optional lower bound. USD total for buy, USD/month for rent.",
            },
            "budget_max": {
                "type": "integer",
                "description": "USD total for buy, USD/month for rent.",
            },
            "neighborhoods": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Preferred LA neighborhoods (e.g. Santa Monica, Venice).",
            },
            "bedrooms": {"type": "integer", "description": "Optional bedroom count."},
            "timeline_months": {
                "type": "integer",
                "description": "Months until they want to move in / close.",
            },
            "financing": {
                "type": "string",
                "enum": ["cash", "conventional", "jumbo", "foreign_national", "rental"],
                "description": "Required for buy intent. Use 'rental' for rent intent.",
            },
            "must_haves": {
                "type": "array",
                "items": {"type": "string"},
                "description": "e.g. parking, pool, dog-friendly, ocean view.",
            },
            "language": {
                "type": "string",
                "enum": ["en", "es"],
                "description": "Language the conversation is happening in.",
            },
            "summary": {
                "type": "string",
                "description": "1–2 sentences summarizing the lead for the agent.",
            },
        },
        "required": [
            "name",
            "intent",
            "budget_max",
            "neighborhoods",
            "timeline_months",
            "summary",
            "language",
        ],
    },
}


@dataclass
class ClaudeReply:
    """One Claude turn — text to send back, plus optional structured lead data."""

    text: str
    lead_data: dict[str, Any] | None = None


async def chat(history: list[dict[str, str]], user_message: str) -> ClaudeReply:
    """Send ``history`` + ``user_message`` to Claude.

    ``history`` is a list of ``{"role": "user" | "assistant", "content": str}``.
    Returns whatever text Claude wants to send to the prospect, plus, if
    Claude decided the lead is qualified, the structured lead data.
    """
    messages: list[dict[str, Any]] = [*history, {"role": "user", "content": user_message}]

    response: Message = await _client.messages.create(
        model=_settings.claude_model,
        max_tokens=_settings.claude_max_tokens,
        system=[
            {
                "type": "text",
                "text": _build_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[RECORD_LEAD_TOOL],
        messages=messages,
    )

    text_chunks: list[str] = []
    lead_data: dict[str, Any] | None = None
    for block in response.content:
        if isinstance(block, TextBlock):
            text_chunks.append(block.text)
        elif isinstance(block, ToolUseBlock) and block.name == "record_lead":
            lead_data = dict(block.input)

    text = "\n".join(c.strip() for c in text_chunks if c.strip())
    if not text:
        text = _default_reply(lead_data)
    return ClaudeReply(text=text, lead_data=lead_data)


def _default_reply(lead_data: dict[str, Any] | None) -> str:
    """Fallback if Claude only returned a tool call with no accompanying text."""
    if lead_data:
        name = lead_data.get("name", "there")
        return f"Got it, {name}! One of our agents will reach out within the hour with options. ✨"
    return "Got it — let me check with an agent. One sec! 🏡"
