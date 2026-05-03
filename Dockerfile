# syntax=docker/dockerfile:1.6
# ---------------------------------------------------------------------------
# Casa Verde Realty — WhatsApp AI Lead Bot
#
# Multi-stage Dockerfile. Stage 1 builds wheels in a fat builder image,
# stage 2 copies just the compiled wheels into a slim runtime — keeps
# the final image around ~120 MB.
# ---------------------------------------------------------------------------

FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build
COPY requirements.txt ./
RUN pip wheel --wheel-dir=/wheels -r requirements.txt


# ---------------------------------------------------------------------------

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Run as non-root user — defence-in-depth.
RUN groupadd --system --gid 1001 botuser \
 && useradd  --system --uid 1001 --gid botuser --create-home botuser

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY --chown=botuser:botuser . ./

# SQLite DB lives in a volume so it survives container rebuilds.
VOLUME ["/data"]
ENV DATABASE_URL=sqlite+aiosqlite:////data/leads.db

USER botuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://127.0.0.1:8000/healthz', timeout=3).raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
