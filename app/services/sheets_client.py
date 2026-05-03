"""Google Sheets CRM — appends one row per qualified lead.

gspread is synchronous; we wrap calls in ``asyncio.to_thread`` to keep the
FastAPI request handler non-blocking.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings

_settings = get_settings()

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS: list[str] = [
    "timestamp_utc",
    "score",
    "score_value",
    "name",
    "phone",
    "email",
    "intent",
    "budget_min_usd",
    "budget_max_usd",
    "neighborhoods",
    "bedrooms",
    "timeline_months",
    "financing",
    "must_haves",
    "language",
    "summary",
]


def _open_sheet() -> gspread.Worksheet:
    """Open the configured worksheet using a service-account credential."""
    creds = Credentials.from_service_account_file(
        str(_settings.google_credentials_json), scopes=_SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(_settings.google_sheets_id).worksheet(_settings.google_sheets_tab)


def _append_row_sync(row: list[Any]) -> None:
    sheet = _open_sheet()
    sheet.append_row(row, value_input_option="USER_ENTERED")


async def append_lead(lead: dict[str, Any], score_label: str, score_value: int) -> None:
    """Append one lead row. Caller is expected to handle exceptions.

    Silently no-ops if ``GOOGLE_SHEETS_ID`` is empty — useful for early
    smoke tests where you want WhatsApp + Claude working before you wire
    up the CRM.
    """
    if not _settings.google_sheets_id:
        return
    row = [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        score_label,
        score_value,
        lead.get("name", ""),
        lead.get("phone", ""),
        lead.get("email", ""),
        lead.get("intent", ""),
        lead.get("budget_min", ""),
        lead.get("budget_max", ""),
        ", ".join(lead.get("neighborhoods", []) or []),
        lead.get("bedrooms", ""),
        lead.get("timeline_months", ""),
        lead.get("financing", ""),
        ", ".join(lead.get("must_haves", []) or []),
        lead.get("language", ""),
        lead.get("summary", ""),
    ]
    await asyncio.to_thread(_append_row_sync, row)


async def ensure_headers() -> None:
    """Idempotent — creates the bold header row if the sheet is empty.

    Silently no-ops when ``GOOGLE_SHEETS_ID`` is empty.
    """
    if not _settings.google_sheets_id:
        return

    def _run() -> None:
        sheet = _open_sheet()
        if sheet.row_values(1):
            return
        sheet.append_row(HEADERS)
        last_col_letter = chr(ord("A") + len(HEADERS) - 1)
        sheet.format(f"A1:{last_col_letter}1", {"textFormat": {"bold": True}})

    await asyncio.to_thread(_run)
