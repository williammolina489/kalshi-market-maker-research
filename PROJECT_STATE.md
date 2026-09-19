# Project State

Last updated: 2026-09-19

## Status

FOUNDATION COMPLETE / E001 PREREGISTERED / PERFORMANCE UNVIEWED

The repository was initialized from an empty state. Current Kalshi rules and APIs were researched from first-party documentation before choosing a research universe or freezing E001.

## Frozen safety boundary

- No live orders.
- No real money.
- No funded execution.
- No trading credentials in Git.
- The implemented client exposes public `GET` methods only.
- E001 may not be evaluated until a prospective collector is implemented and its evidence window begins after the preregistration commit.

## Initial universe

`KXHIGHNY` — Highest temperature in NYC, a daily recurring Climate and Weather series.

Selection is structural, not return-based: recurring daily events, objective published settlement source, standardized bucket markets, public metadata/order books/trades, and enough current public activity to justify prospective observation. E001 still requires two-sided depth and spread gates at each hypothetical quote decision.

## Current blockers / unresolved items

1. Kalshi's public Trade API does not expose historical full order-book depth; E001 therefore requires prospective capture.
2. WebSocket sessions require authentication even for public market-data channels. E001 does not require WebSockets initially: the planned collector can use unauthenticated public REST polling. If WebSockets are later used, credentials must be least-privilege and remain outside Git.
3. No single universal numeric position limit was found in the public market/series API schema. Limits may be product/member specific; designated market makers can receive adjusted position limits. Before any future live-execution proposal, contract-specific and account-specific limits must be re-verified.
4. Liquidity incentives are temporary and mutable. Simulated reward estimates are secondary only and cannot make E001 pass.

## Exact next step

Implement a read-only prospective collector that writes immutable raw observations for `KXHIGHNY` using public REST endpoints, then run a non-performance 24-hour integrity smoke test. Only after integrity review should the 30-calendar-day E001 evidence window be started. Do not compute E001 P/L during the smoke test.
