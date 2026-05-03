"""Tests for the conversation orchestrator with Claude / Sheets / Slack mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.services import conversation
from app.services.claude_client import ClaudeReply
from app.storage.models import Conversation, Lead, Message


@pytest.mark.asyncio
async def test_first_message_creates_conversation(session) -> None:
    fake_reply = ClaudeReply(text="Hi! Buy or rent?")
    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(return_value=fake_reply)),
        patch("app.services.conversation.sheets_client.append_lead", AsyncMock()),
        patch("app.services.conversation.slack_client.notify_lead", AsyncMock()),
    ):
        reply = await conversation.handle_inbound(session, phone="+14155550100", body="Hello")
    await session.commit()

    assert reply == "Hi! Buy or rent?"
    convs = (await session.execute(select(Conversation))).scalars().all()
    assert len(convs) == 1
    assert convs[0].phone_number == "+14155550100"


@pytest.mark.asyncio
async def test_messages_are_persisted(session) -> None:
    fake_reply = ClaudeReply(text="Got it — Westside is great. What's your budget?")
    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(return_value=fake_reply)),
        patch("app.services.conversation.sheets_client.append_lead", AsyncMock()),
        patch("app.services.conversation.slack_client.notify_lead", AsyncMock()),
    ):
        await conversation.handle_inbound(session, phone="+14155550100", body="I want to buy")
    await session.commit()

    msgs = (await session.execute(select(Message))).scalars().all()
    assert {(m.role, m.content) for m in msgs} == {
        ("user", "I want to buy"),
        ("assistant", "Got it — Westside is great. What's your budget?"),
    }


@pytest.mark.asyncio
async def test_qualified_lead_is_recorded_and_scored_hot(session, hot_lead_buy) -> None:
    sheets_mock = AsyncMock()
    slack_mock = AsyncMock()
    fake_reply = ClaudeReply(text="Got it, Carlos! ✨", lead_data=hot_lead_buy)
    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(return_value=fake_reply)),
        patch("app.services.conversation.sheets_client.append_lead", sheets_mock),
        patch("app.services.conversation.slack_client.notify_lead", slack_mock),
    ):
        await conversation.handle_inbound(
            session, phone="+14155550100", body="$2.5M Westside, foreign national"
        )
    await session.commit()

    leads = (await session.execute(select(Lead))).scalars().all()
    assert len(leads) == 1
    lead = leads[0]
    assert lead.score == "HOT"
    assert lead.score_value >= 80
    assert lead.name == "Carlos Reyes"
    assert lead.language == "es"
    assert lead.neighborhoods == ["Santa Monica", "Brentwood"]
    sheets_mock.assert_awaited_once()
    slack_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_cold_lead_still_recorded(session, cold_lead_browse) -> None:
    sheets_mock = AsyncMock()
    slack_mock = AsyncMock()
    fake_reply = ClaudeReply(text="Got it!", lead_data=cold_lead_browse)
    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(return_value=fake_reply)),
        patch("app.services.conversation.sheets_client.append_lead", sheets_mock),
        patch("app.services.conversation.slack_client.notify_lead", slack_mock),
    ):
        await conversation.handle_inbound(session, phone="+14155550101", body="just browsing")
    await session.commit()

    leads = (await session.execute(select(Lead))).scalars().all()
    assert len(leads) == 1
    assert leads[0].score == "COLD"
    sheets_mock.assert_awaited_once()
    # Slack mock is still called — the slack_client itself decides whether to actually post
    slack_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_history_is_passed_to_claude(session) -> None:
    """Subsequent messages should include the prior turn in Claude's history."""
    captured_histories: list[list[dict]] = []

    async def capture(history, user_message):
        captured_histories.append(list(history))
        return ClaudeReply(text="ok")

    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(side_effect=capture)),
        patch("app.services.conversation.sheets_client.append_lead", AsyncMock()),
        patch("app.services.conversation.slack_client.notify_lead", AsyncMock()),
    ):
        await conversation.handle_inbound(session, phone="+14155550102", body="hi")
        await conversation.handle_inbound(session, phone="+14155550102", body="2br venice")
    await session.commit()

    assert captured_histories[0] == []
    assert captured_histories[1] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "ok"},
    ]


@pytest.mark.asyncio
async def test_sheets_failure_does_not_block_reply(session, hot_lead_buy) -> None:
    """Sheets/Slack errors should be swallowed — the user must always get a reply."""
    fake_reply = ClaudeReply(text="Got it, Carlos! ✨", lead_data=hot_lead_buy)
    with (
        patch("app.services.conversation.claude_client.chat", AsyncMock(return_value=fake_reply)),
        patch(
            "app.services.conversation.sheets_client.append_lead",
            AsyncMock(side_effect=RuntimeError("sheets down")),
        ),
        patch("app.services.conversation.slack_client.notify_lead", AsyncMock()),
    ):
        reply = await conversation.handle_inbound(
            session, phone="+14155550103", body="2.5M cash 2 months"
        )
    await session.commit()

    assert reply == "Got it, Carlos! ✨"
    leads = (await session.execute(select(Lead))).scalars().all()
    assert len(leads) == 1, "lead must still be persisted even if Sheets fails"
