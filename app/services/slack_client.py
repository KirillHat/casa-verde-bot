"""Slack notifications via incoming-webhook URL, with score-based filtering."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger()
_settings = get_settings()

_SCORE_RANK: dict[str, int] = {"HOT": 3, "WARM": 2, "COLD": 1}
_EMOJI: dict[str, str] = {"HOT": "\U0001f525", "WARM": "\U0001f7e1", "COLD": "\U0001f535"}


async def notify_lead(lead: dict[str, Any], score: str, score_value: int) -> bool:
    """Post a lead card to Slack. Returns True if a notification was sent."""
    if not _settings.slack_notify_enabled or not _settings.slack_webhook_url:
        return False
    if _SCORE_RANK[score] < _SCORE_RANK[_settings.slack_notify_min_score]:
        return False

    emoji = _EMOJI[score]
    intent = (lead.get("intent") or "?").upper()
    budget_max = lead.get("budget_max") or 0
    budget_str = f"${budget_max:,}" if intent == "BUY" else f"${budget_max:,}/mo"
    neighborhoods = ", ".join(lead.get("neighborhoods") or []) or "any"
    timeline = lead.get("timeline_months", "?")
    name = lead.get("name", "Unknown")
    phone = lead.get("phone", "")
    summary = lead.get("summary", "")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {score} lead — {name}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Intent*\n{intent} · {neighborhoods}"},
                {"type": "mrkdwn", "text": f"*Budget*\n{budget_str}"},
                {"type": "mrkdwn", "text": f"*Timeline*\n{timeline} months"},
                {"type": "mrkdwn", "text": f"*Phone*\n{phone}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f">_{summary}_"},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"score `{score_value}` · lang `{lead.get('language', 'en')}` · "
                        f"{_settings.business_name}"
                    ),
                }
            ],
        },
    ]

    payload = {"text": f"{emoji} {score} lead from {name}", "blocks": blocks}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            _settings.slack_webhook_url.get_secret_value(),
            json=payload,
        )
    if resp.status_code != 200:
        log.warning("slack.notify_non_200", status=resp.status_code, body=resp.text)
    return resp.status_code == 200
