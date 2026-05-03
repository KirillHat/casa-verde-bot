"""One-shot script to create the header row in the Google Sheet.

Run after configuring `GOOGLE_SHEETS_ID` and `GOOGLE_CREDENTIALS_JSON` in `.env`:

    python scripts/setup_sheets.py
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.services.sheets_client import _open_sheet, ensure_headers


async def main() -> None:
    settings = get_settings()
    print(f"→ Connecting to sheet ID: {settings.google_sheets_id}")
    sheet = _open_sheet()
    print(f"✓ Connected to sheet: {sheet.spreadsheet.title}")
    print(f"✓ Tab '{sheet.title}' found")
    await ensure_headers()
    cols = len(sheet.row_values(1))
    print(f"✓ Headers ensured (sheet has {cols} columns)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"✗ Failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
