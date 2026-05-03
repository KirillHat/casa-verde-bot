"""Twilio WhatsApp webhook — receives inbound messages from prospects.

Pattern: ack the webhook in <100ms with empty TwiML, then process the
message in a background task and send the reply via the Twilio REST API.
This keeps Twilio happy regardless of how slow Claude is on a given turn.
"""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient

from app.config import get_settings
from app.services import conversation
from app.storage.db import session_scope

log = structlog.get_logger()
router = APIRouter()

_settings = get_settings()
_validator = RequestValidator(_settings.twilio_auth_token.get_secret_value())
_twilio = TwilioClient(
    _settings.twilio_account_sid,
    _settings.twilio_auth_token.get_secret_value(),
)


def _strip_whatsapp_prefix(addr: str) -> str:
    """Convert ``whatsapp:+14155550100`` → ``+14155550100``."""
    return addr.replace("whatsapp:", "", 1)


async def _validate_signature(request: Request) -> None:
    """Reject any request whose X-Twilio-Signature doesn't match.

    Skippable in dev with ``DEBUG_SKIP_TWILIO_SIGNATURE=true``. The flag
    is read via ``get_settings()`` (not the module-level cache) so tests
    can flip it after import time.
    """
    if get_settings().debug_skip_twilio_signature:
        return
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}
    if not _validator.validate(url, params, signature):
        log.warning("twilio.invalid_signature", url=url)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.post("/webhooks/whatsapp", response_class=Response)
async def whatsapp_webhook(
    request: Request,
    background: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form(""),
    WaId: str = Form(""),
) -> Response:
    """Receive a WhatsApp message and ack immediately. Reply asynchronously."""
    await _validate_signature(request)

    phone = _strip_whatsapp_prefix(From)
    log.info("whatsapp.inbound", phone=phone, profile=ProfileName, body_len=len(Body))

    background.add_task(_process_and_reply, phone=phone, body=Body)
    return Response(status_code=200, media_type="application/xml", content="<Response/>")


async def _process_and_reply(*, phone: str, body: str) -> None:
    """Run the LLM + persistence + outbound message in the background."""
    try:
        async with session_scope() as session:
            reply_text = await conversation.handle_inbound(session, phone=phone, body=body)
        await asyncio.to_thread(_send_whatsapp, to=phone, body=reply_text)
    except Exception as exc:
        log.exception("whatsapp.processing_failed", error=str(exc), phone=phone)


def _send_whatsapp(*, to: str, body: str) -> None:
    """Synchronous Twilio call — wrapped in to_thread by the caller."""
    _twilio.messages.create(
        from_=_settings.twilio_whatsapp_from,
        to=f"whatsapp:{to}",
        body=body,
    )


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
