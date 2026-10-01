# Project State

Last updated: 2026-10-01

## Status

FOUNDATION COMPLETE / COLLECTOR REBUILT / E001 PREREGISTERED / PERFORMANCE UNVIEWED / NOT RUNNING

The clean replacement collector is labeled **REBUILT FROM CANONICAL E001 SPECIFICATION**. The exact prior implementation was lost; this is not a recovery claim. Current Kalshi runtime evidence and the frozen preregistration remain authoritative.

## Frozen safety boundary

- No live orders.
- No real money.
- No funded execution.
- No trading credentials in Git.
- The implemented client exposes public `GET` methods only.
- E001 may not be evaluated until the separate infrastructure gate passes and its evidence window begins after the preregistration commit.

## Initial universe

`KXHIGHNY` — Highest temperature in NYC, a daily recurring Climate and Weather series.

Selection is structural, not return-based: recurring daily events, objective published settlement source, standardized bucket markets, public metadata/order books/trades, and enough current public activity to justify prospective observation. E001 still requires two-sided depth and spread gates at each hypothetical quote decision.

## Current blockers / unresolved items

1. Kalshi's public Trade API does not expose historical full order-book depth; E001 therefore requires prospective capture.
2. WebSocket sessions require authentication even for public market-data channels. E001 does not require WebSockets initially: the collector uses unauthenticated public REST polling. If WebSockets are later used, credentials must be least-privilege and remain outside Git.
3. No single universal numeric position limit was found in the public market/series API schema. Limits may be product/member specific; designated market makers can receive adjusted position limits. Before any future live-execution proposal, contract-specific and account-specific limits must be re-verified.
4. Liquidity incentives are temporary and mutable. Simulated reward estimates are secondary only and cannot make E001 pass.

## Rebuild status

- Immutable compressed JSONL storage, manifests, deterministic replay, restart state, cadence definitions, conservative queue/inventory simulation, and performance-blinded smoke reporting are implemented.
- Rebuild PR #1 was reviewed and merged as `04ef07ffb2106e6b96807de86727665185e72e15`; post-merge CI passed.
- Manual-only smoke tooling exists but has not been run. No 24-hour smoke or 30-day E001 window has started.
- The first-party orderbook authentication rendering versus unauthenticated Stage-0 runtime behavior is documented in `research/API_CONTRACT_REVALIDATION.md`.

## Exact next step

The rebuild PR was reviewed and merged on 2026-10-01. The next gate is an explicitly authorized non-performance 24-hour integrity smoke test. The smoke has not started. Only after integrity review should the 30-calendar-day E001 evidence window be started. Do not compute E001 P/L during the smoke test.
