# Project State

Last updated: 2026-10-12

## Status

FOUNDATION COMPLETE / COLLECTOR REBUILT AND POLLING HARDENED / FIRST 24H SMOKE COMPLETE — INTEGRITY REVIEW REQUIRED / E001 PREREGISTERED / PERFORMANCE UNVIEWED / 30D NOT RUNNING

The clean replacement collector is **REBUILT FROM CANONICAL E001 SPECIFICATION**.
The exact prior implementation was lost; the rebuild is not an exact recovery.

## Frozen safety boundary

- No live orders, funded execution, or real money.
- No trading credentials or authenticated order client.
- Public HTTPS GET observation only.
- Only the original non-performance 24-hour smoke was authorized on 2026-10-01.
- The 30-calendar-day E001 evidence period has **not** been authorized or started.
- E001 economic performance is **unviewed** and must remain so.

## Completed infrastructure smoke

The previously authorized run [36944108882](https://github.com/williammolina489/kalshi-market-maker-research/actions/runs/36944108882) completed on 2026-10-03; all five chunks and its immutable-replay/integrity-review job succeeded operationally.

The performance-blinded `e001-smoke-integrity-review` artifact reports:

- `wall_clock_window_complete=true`
- `integrity_review_status=REVIEW_REQUIRED`
- **10,698 cadence-gap records** (`cadence_gap_records`); one gap record may represent multiple missed scheduled slots
- **10,698 error-bearing records** (`records_with_errors`), consisting of those cadence-gap records
- Immutable segments and review artifact remain preserved. These observations must not be rewritten, selectively excluded or backfilled.

A successful workflow/replay **does not** establish the frozen 99.5% order-book coverage gate or justify economic evaluation.

## Infrastructure remediation

On 2026-10-12 PR #5 updated the future public read-only collector so 1-Hz order-book and trade GET calls overlap, including overlap with slower metadata/status requests. Gzip append writes are serialized; batch market identity is snapshotted; concurrency and replay regression tests passed. The frozen polling cadence, E001 methodology and prior evidence are unchanged.

On 2026-10-12 PR #6 added per-stream **missed scheduled slot** accounting, distinguishing actual missing samples from their aggregated gap-record count.

On 2026-10-12 PR #7 fixed another documented overhead problem: inspection of the original state-5 artifact showed a 178,201,225-byte `restart.json` with 3,873,924 exchange-wide persisted trade IDs, rewritten by the runner every five seconds. The raw global trade payloads and cursor checks are still fully preserved, but only `KXHIGHNY-` trade IDs now enter the dedup checkpoint, while the watermark continues tracking all returned global trade timestamps. See `docs/SMOKE_RESTART_STATE_INCIDENT_2026-10-12.md`. All PR #7 CI and public read-only preflight checks passed.

These are preventive code improvements, **not** proof of adequate future capture. The original 10,698 gap records remain valid historical evidence, and a separately authorized, bounded non-performance verification run is still required before claiming a passed smoke.

## Current blocker and exact next step

1. Complete integrity-only interpretation of the existing smoke, including per-stream missed scheduled slot totals and their timing. Treat the recorded gaps as genuine missing observations rather than silently fixing the data.
2. If the owner explicitly authorizes a **new, separately scoped non-performance infrastructure verification run**, freeze its dates, identity, storage retention and pass/fail plan first; do not reuse the October 1 authorization marker or the original run.
3. Only after an adequately verified smoke and a further explicit E001 start decision may the official untouched 30-day evidence window begin.

Until then E001 stays PREREGISTERED / NOT RUNNING. Do not calculate strategy P/L, fill economics or promotion metrics.
