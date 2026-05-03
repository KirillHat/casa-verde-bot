# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-05-02

Initial release — production-ready WhatsApp AI lead qualifier for boutique
real-estate, framed as a case study for the fictional *Casa Verde Realty*
(Santa Monica, CA).

### Added
- FastAPI + Twilio WhatsApp webhook with signed-request validation
- Async background processing — webhook acks Twilio in <100 ms regardless
  of LLM latency
- Anthropic Claude integration with **prompt caching** and **tool use**
  (`record_lead`) for strict qualification flow
- LA-tuned deterministic lead-scoring rubric (HOT / WARM / COLD)
- Google Sheets CRM integration with auto-created header row
- Slack incoming-webhook notifications with Block Kit cards and score-based
  filtering (`SLACK_NOTIFY_MIN_SCORE`)
- SQLAlchemy 2.0 async + aiosqlite for conversation memory across restarts
- Bilingual qualifier prompt (English + Spanish, language mirroring)
- pytest test suite covering scoring rules, conversation flow with mocked
  Claude, and webhook signature validation
- GitHub Actions CI: pytest matrix across Python 3.10 / 3.11 / 3.12 +
  ruff lint and format check
- Multi-stage Dockerfile (~120 MB final image, non-root user) +
  `docker-compose.yml`
- `render.yaml` for one-click deploy on Render's free tier
- Utility scripts: `scripts/setup_sheets.py`, `scripts/seed_demo.py`
- Documentation: case study, architecture, Twilio setup, Google Sheets setup
