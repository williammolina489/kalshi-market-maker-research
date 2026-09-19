# Roadmap

## Phase 0 — Current environment research

Complete 2026-09-19. Re-verify operational rules before every experiment that depends on them.

## Phase 1 — Foundation

Complete: documentation, package scaffold, read-only public API client, economics primitives, tests, and CI.

## Phase 2 — Prospective collector

Next. Collect immutable raw market metadata, full available order-book depth, public trades, exchange status, and incentive definitions. Store raw observations separately from derived analytics. Never backfill missing book states from future observations.

## Phase 3 — E001 integrity smoke test

Run 24 hours without calculating strategy performance. Verify timestamp discipline, pagination continuity, market lifecycle handling, quote-window coverage, and provenance. Fix collector defects before the preregistered evidence window.

## Phase 4 — E001 prospective evidence

Run the frozen 30-calendar-day policy in `research/E001_PREREGISTRATION.md`. No parameter sweeps, no post-hoc universe changes, and no peeking for tuning.

## Phase 5 — Decision

Record PASS or STOP / REJECT in `EXPERIMENTS.md`. Preserve the failed specification if rejected. Any materially different quoting policy becomes a new preregistered experiment.

## Future architecture gate

A real execution adapter is intentionally absent. It may only be designed after prospective evidence justifies further work and an explicit project decision approves that phase. Real-money execution remains prohibited under the current project charter.
