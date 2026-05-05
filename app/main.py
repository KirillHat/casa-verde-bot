"""FastAPI application factory + lifespan.

Run locally with: ``uvicorn app.main:app --reload --port 8000``
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

import sentry_sdk
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.config import get_settings
from app.observability import MetricsStore
from app.services.sheets_client import ensure_headers
from app.storage.db import init_db
from app.webhooks import whatsapp


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings.log_level)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )
    await init_db()
    try:
        await ensure_headers()
    except Exception as exc:
        # Sheets may not be reachable in test/dev — log but don't crash
        structlog.get_logger().warning("sheets.headers_skipped", error=str(exc))
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.business_name} — WhatsApp Lead Bot",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.metrics = MetricsStore()

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        bind_contextvars(request_id=request_id)
        start = perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            app.state.metrics.observe(
                method=request.method,
                path=route_path,
                status=status_code,
                duration_seconds=perf_counter() - start,
            )
            clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(whatsapp.router)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(
            app.state.metrics.render_prometheus(),
            media_type="text/plain; version=0.0.4",
        )

    return app


app = create_app()
