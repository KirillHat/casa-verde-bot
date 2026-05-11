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
from fastapi.responses import HTMLResponse, PlainTextResponse
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

    @app.get("/", include_in_schema=False)
    async def index() -> HTMLResponse:
        return HTMLResponse(
            f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{settings.business_name} — WhatsApp AI Lead Bot</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif; max-width: 720px; margin: 4rem auto; padding: 0 1.5rem; color: #1f2937; line-height: 1.55; }}
  h1 {{ font-size: 1.75rem; margin-bottom: .25rem; }}
  .tag {{ display: inline-block; background: #25D366; color: #fff; padding: .15rem .55rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }}
  .muted {{ color: #6b7280; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul {{ padding-left: 1.25rem; }}
  code {{ background: #f3f4f6; padding: .1rem .35rem; border-radius: 4px; font-size: .92em; }}
  hr {{ border: 0; border-top: 1px solid #e5e7eb; margin: 2rem 0; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }}
  .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; }}
  .card h3 {{ margin-top: 0; font-size: .95rem; }}
</style>
</head>
<body>
<p><span class="tag">WhatsApp Business</span> <span class="muted">production demo</span></p>
<h1>{settings.business_name} — AI Lead Bot</h1>
<p class="muted">Production-style WhatsApp assistant that auto-replies to inbound real-estate leads in under 30 seconds, qualifies them via bilingual (EN/ES) conversation, scores them HOT/WARM/COLD, and pushes the lead into Google Sheets + Slack.</p>

<p><strong>This URL is the backend API.</strong> To try the bot, message it on WhatsApp — see the GitHub README for the Twilio sandbox join code.</p>

<div class="grid">
  <div class="card">
    <h3>📚 API docs</h3>
    <p><a href="/docs">Swagger UI</a> · <a href="/redoc">ReDoc</a></p>
  </div>
  <div class="card">
    <h3>❤️ Health & metrics</h3>
    <p><a href="/healthz">/healthz</a> · <a href="/metrics">/metrics</a></p>
  </div>
  <div class="card">
    <h3>💻 Source code</h3>
    <p><a href="https://github.com/KirillHat/casa-verde-bot">github.com/KirillHat/casa-verde-bot</a></p>
  </div>
  <div class="card">
    <h3>📩 Webhook</h3>
    <p><code>POST /webhooks/whatsapp</code> (Twilio signed)</p>
  </div>
</div>

<hr>
<p class="muted" style="font-size: .85rem;">Casa Verde Realty is a fictional but realistic boutique agency used as an end-to-end portfolio demo. The codebase is real, the system is deployed, and the architecture transfers directly to any client niche (yoga studios, solar installers, dental practices, etc.) in 1–2 days.</p>
</body>
</html>"""
        )

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(
            app.state.metrics.render_prometheus(),
            media_type="text/plain; version=0.0.4",
        )

    return app


app = create_app()
