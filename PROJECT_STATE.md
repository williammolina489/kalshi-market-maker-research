# Project State

Last updated: 2026-10-01

## Status

FOUNDATION COMPLETE / COLLECTOR REBUILT / 24H SMOKE RUNNING / E001 PREREGISTERED / PERFORMANCE UNVIEWED / 30D NOT RUNNING

The clean replacement collector is labeled REBUILT FROM CANONICAL E001 SPECIFICATION.
The exact prior implementation was lost; this is not a recovery claim. Current Kalshi
runtime evidence and the frozen preregistration remain authoritative.

## Frozen safety boundary

- No live orders.
- No real money.
- No funded execution.
- No trading credentials in Git.
- The implemented client exposes public GET methods only.
- The project owner authorized one non-performance 24-hour infrastructure smoke on
  2026-10-01.
- The official 30-calendar-day E001 evidence window is not authorized and remains stopped.
- E001 economic performance remains unviewed.

## Initial universe

KXHIGHNY — Highest temperature in NYC, a daily recurring Climate and Weather series.

Selection is structural, not return-based: recurring daily events, objective published
settlement source, standardized bucket markets, public metadata/order books/trades, and
enough current public activity to justify prospective observation. E001 still requires
two-sided depth and spread gates at each hypothetical quote decision.

## Rebuild and smoke status

- Rebuild PR #1 was reviewed and merged as
  04ef07ffb2106e6b96807de86727665185e72e15; post-merge CI passed.
- Status PR #2 recorded the separate smoke authorization gate.
- The owner has now authorized only the 24-hour non-performance integrity smoke.
- The smoke runtime uses bounded chunks, immutable compressed JSONL segments, cumulative
  SHA-256 manifests, restart state, explicit cadence gaps, and performance-blinded review.
- Smoke launch PR #3 merged as `6daccf95955c18a2efbb9b78f3d144c3779dedff`.
- GitHub Actions run `36944108882` started the authorized 24-hour smoke; chunk 1 is running.
- No 30-day E001 evidence collection or performance evaluation is authorized.

## Current blockers / unresolved items

1. The smoke must complete its full wall-clock interval and immutable replay.
2. Any unresolved cursor gap, corrupted segment, missing required metadata, or cadence
   integrity failure stops/rejects the smoke evidence; no favorable backfill is allowed.
3. Only after smoke integrity review may a separate decision be made about the official
   30-day E001 window.

## Exact next step

Continue only the already-started 24-hour non-performance infrastructure smoke through
its bounded chunks and integrity-only final review. Do not calculate E001 economic
performance and do not start the official 30-day evidence window.
