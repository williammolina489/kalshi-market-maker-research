# Kalshi Market Maker Research

Research-only project for testing whether passive prediction-market quoting can have positive executable expected value after realistic fills, adverse selection, fees, inventory costs, and capital opportunity cost.

## Safety boundary

**Real-money trading is prohibited.** This repository contains no funded execution adapter, no order-placement method, and no credential-loading path for trading. The only implemented network client is read-only and uses public `GET` market-data endpoints.

## Current state

- Phase 0 current-environment research: complete as of 2026-09-19.
- Foundation scaffold: complete.
- E001 — Prospective Passive-Quote Viability: **PREREGISTERED, NOT RUN**.
- Initial research universe: `KXHIGHNY` (daily NYC high-temperature series), subject to the frozen market-state eligibility gates in the E001 preregistration.
- Performance has not been calculated or viewed.

See `PROJECT_STATE.md`, `research/KALSHI_CURRENT_RESEARCH.md`, and `research/E001_PREREGISTRATION.md`.

## Local checks

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

Optional public-API smoke test (read-only, no API key):

```bash
python -m kalshi_mm.validate_public_api
```

## Repository rule

GitHub is the permanent source of truth. Research decisions, frozen assumptions, failures, and results belong in this repository rather than in chat history.
