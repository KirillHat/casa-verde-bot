"""Shared pytest fixtures.

Sets dummy env vars BEFORE any app module is imported, so pydantic-settings
doesn't blow up trying to read missing required values.
"""

from __future__ import annotations

import os

# --- Dummy env vars (must be set before importing app.*) ---------------------
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest_account_sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth_token")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("GOOGLE_SHEETS_ID", "test_sheet_id")
os.environ.setdefault("GOOGLE_CREDENTIALS_JSON", "/tmp/nonexistent_credentials.json")
os.environ.setdefault("SLACK_NOTIFY_ENABLED", "false")
os.environ.setdefault("DEBUG_SKIP_TWILIO_SIGNATURE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.storage.models import Base  # noqa: E402


@pytest_asyncio.fixture
async def session():
    """Provide a fresh in-memory SQLite session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def hot_lead_buy() -> dict:
    """Carlos — Mexican buyer, $2.5M Westside, foreign-national loan, 2 mo timeline."""
    return {
        "name": "Carlos Reyes",
        "email": "carlos@example.com",
        "intent": "buy",
        "budget_min": 2_000_000,
        "budget_max": 2_500_000,
        "neighborhoods": ["Santa Monica", "Brentwood"],
        "bedrooms": 3,
        "timeline_months": 2,
        "financing": "foreign_national",
        "must_haves": ["pool", "ocean view"],
        "language": "es",
        "summary": "Mexican buyer, $2.5M, 3BR Westside, foreign national loan, 2 months.",
    }


@pytest.fixture
def warm_lead_rent() -> dict:
    """Sarah — NYC tech mover, 2BR rental Venice, $5k/mo, Sept 1."""
    return {
        "name": "Sarah Chen",
        "intent": "rent",
        "budget_max": 5_000,
        "neighborhoods": ["Venice", "Silver Lake"],
        "bedrooms": 2,
        "timeline_months": 1,
        "financing": "rental",
        "must_haves": ["walk to coffee shops", "unfurnished"],
        "language": "en",
        "summary": "NYC mover joining Google, 2BR Venice/Silver Lake $5k/mo, Sept 1.",
    }


@pytest.fixture
def cold_lead_browse() -> dict:
    """Anonymous browser, $600k, no timeline."""
    return {
        "name": "Browser",
        "intent": "buy",
        "budget_max": 600_000,
        "neighborhoods": [],
        "timeline_months": 24,
        "financing": None,
        "language": "en",
        "summary": "Just browsing, low budget, no timeline.",
    }
