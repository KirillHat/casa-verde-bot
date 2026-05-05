"""Async database engine, session factory, and one-shot schema bootstrap."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.storage.models import Base

_settings = get_settings()


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create the parent directory for a SQLite file URL if missing.

    Without this, fresh deploys fail at startup with `unable to open
    database file` because the SQLAlchemy engine doesn't create directories.
    No-op for non-SQLite URLs and for the special ``:memory:`` URL.
    """
    if not database_url.startswith("sqlite"):
        return
    # Strip dialect+driver prefix → file path. Examples:
    #   sqlite+aiosqlite:///./data/leads.db   → ./data/leads.db
    #   sqlite+aiosqlite:////tmp/leads.db     → /tmp/leads.db
    #   sqlite+aiosqlite:///:memory:          → :memory:
    _, _, path_part = database_url.partition(":///")
    if not path_part or path_part == ":memory:":
        return
    parent = Path(path_part).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_dir(_settings.database_url)

engine = create_async_engine(_settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create the schema on first run. No migrations — single-process app."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield a session with automatic commit / rollback on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
