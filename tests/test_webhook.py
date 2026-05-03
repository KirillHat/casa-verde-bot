"""Tests for the Twilio webhook endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_webhook_acks_immediately(client: TestClient) -> None:
    """Webhook returns 200 + empty TwiML; processing is dispatched in background."""
    with patch("app.webhooks.whatsapp._process_and_reply", new=AsyncMock()) as proc:
        r = client.post(
            "/webhooks/whatsapp",
            data={
                "From": "whatsapp:+14155550100",
                "Body": "Hi, looking for a 2BR rental in Venice",
                "ProfileName": "Test User",
                "WaId": "14155550100",
            },
        )

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    assert "<Response/>" in r.text
    proc.assert_awaited_once()
    call_kwargs = proc.await_args.kwargs
    assert call_kwargs["phone"] == "+14155550100"
    assert "Venice" in call_kwargs["body"]


def test_webhook_strips_whatsapp_prefix(client: TestClient) -> None:
    with patch("app.webhooks.whatsapp._process_and_reply", new=AsyncMock()) as proc:
        client.post(
            "/webhooks/whatsapp",
            data={"From": "whatsapp:+14155550199", "Body": "hola"},
        )
    assert proc.await_args.kwargs["phone"] == "+14155550199"


def test_webhook_signature_required(monkeypatch) -> None:
    """When sig validation is on, an unsigned/wrong-sig request is rejected with 403."""
    monkeypatch.setenv("DEBUG_SKIP_TWILIO_SIGNATURE", "false")
    get_settings.cache_clear()
    try:
        app_client = TestClient(create_app())
        r = app_client.post(
            "/webhooks/whatsapp",
            data={"From": "whatsapp:+1", "Body": "x"},
            headers={"X-Twilio-Signature": "definitely-wrong"},
        )
        assert r.status_code == 403
    finally:
        get_settings.cache_clear()
