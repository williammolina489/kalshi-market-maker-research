# Proposed E001 Infrastructure Smoke Verification V2 — Approval Required

**Draft prepared:** 2026-10-13  
**Current state:** PROPOSAL ONLY — NOT PREREGISTERED, AUTHORIZED, SCHEDULED, OR RUNNING  
**Permitted scope if separately authorized:** public, unauthenticated HTTPS GET observation; integrity only  
**Explicitly excluded:** orders, credentials, real money, strategy economics, official E001 30-day evidence, market/strategy changes

## Why another infrastructure-only test is needed

The original, one-time-authorized October 2–3 E001 smoke [GitHub Actions run 36944108882](https://github.com/williammolina489/kalshi-market-maker-research/actions/runs/36944108882) completed and passed immutable replay but produced `REVIEW_REQUIRED`, not a data-integrity pass. Its untouched review artifact reports:

| Raw source | Recorded rows |
| --- | ---: |
| orderbooks_batch | 10,597 |
| trades_global | 12,304 |
| markets | 780 |
| exchange_status | 4,267 |
| incentives | 3,487 |
| cadence_gap | 10,698 |

The frozen quote window 09:00–15:30 ET is six hours and thirty minutes: approximately **23,400 one-second book-poll opportunities** per complete eligible day. The **10,597** recorded book batches across the complete October 2 window cannot meet the frozen **99.5%** requirement, even before invalid/missing-market batches are excluded. This is infrastructure evidence, **not** an E001 economic evaluation. Gap records may each represent multiple missed slots.

The original state-5 artifact also held **3,873,924 exchange-wide trade IDs** in a ~178 MB checkpoint, repeatedly saved every five seconds. That is an independently verified overhead defect, but its contribution to each missed slot cannot be apportioned from the aggregate review alone.

## Implemented remedies to verify, not retroactively credit

1. **PR #5** overlaps independent public book/trade requests while serializing immutable compressed JSONL writes.
2. **PR #6** reports actual missed scheduled poll **slots** by stream, rather than relying only on cadence-gap record count.
3. **PR #7** limits persisted trade-ID dedup state to frozen `KXHIGHNY-` markets while retaining full raw global trade pages, trade identity checks, cursor lineage and the global coverage watermark.
4. All three changes merged with passing CI. None supplies prospective evidence of a 99.5% book coverage rate, and none repairs the October 2 source records.

## Separate future smoke proposal

Only following explicit project-owner approval, create a **new** immutable authorization identity and fresh prospective times in a *separate* authorization artifact. Do not modify or retrigger `research/E001_SMOKE_AUTHORIZATION.json` or claim the old authorization covers a replacement run.

**Before any public-data collection:**

- Freeze the new `verification_id`, `collector_commit_sha`, start/deadline (exactly 24h), New York quote windows, allowed GET-only endpoints, artifact-retention settings, and expected-runner plan.
- Verify the commit and CI pass; run only a short preflight that performs no strategy-economics work. Check that required public endpoints are reachable, that the runner can begin before the intended sampling window, and that a 24h chunk/restart workflow can retain its state.
- Require a fail-closed launch gate. No fallback to expired windows, backfilled market data, synthetic samples, skipped trade pages, filtered bad markets, or different series.
- Confirm GitHub Actions public-repository standard runner minute cost and separately check storage retention/quota before authorizing a long test. Do not purchase extra capacity or change repository visibility or secrets.
- If GitHub Actions is degraded or an intended start has passed, stop at a human gate. Do not silently shift the experiment's time period.

**During the 24h smoke:**

- Observe only the existing frozen `KXHIGHNY` public-data streams and 09:00–15:30 ET quote window.
- Preserve raw returned payloads, UTC request/receive/scheduled timestamps, full pages, trade cursor/watermark state, failures and gap records.
- Track runtime checkpoint size, save duration, per-stream latency, and number of scheduled/attempted/successful **slots**. These are operational metrics only.
- Keep SHA-256 manifests and compressed JSONL segments immutable. Do not calculate strategy return, P/L, fills, drawdown, incentive value, or promote E001.

**Review criteria:**

- The entire 24h wall-clock run and at least one complete 09:00–15:30 ET quote window must finish.
- Compute unique successful scheduled order-book slots divided by all eligible 1-Hz slots; demand at least **99.5%**, using the unchanged frozen requirement. Fail closed for missing or corrupt expected batch markets, missing raw records, non-monotonic source timestamps, invalid trade cursor lineage, failed hashes or broken manifest replay.
- Report individual streams' expected, attempted, valid, failed, and missing scheduled slots. Do not infer successful sampling from a `cadence_gap` row count or from an Actions `success` conclusion.
- Review whether checkpoint-state size and saving time stayed bounded and whether missing slots correlate with network latency or restarts. Do not infer from count summaries that the cause is solved.
- The result is `INFRASTRUCTURE VERIFIED` or `INFRASTRUCTURE NOT VERIFIED`, **not** an E001 strategy PASS/FAIL.

## Separate E001 authorization still required

Even if this *separate* smoke passes, official E001 30-consecutive-calendar-day evidence collection remains **NOT STARTED** and requires a later explicit owner start decision. Economic performance inspection and real-money trading remain prohibited. E002 is not created here.

## Decision needed

The owner may choose to approve the preparation of a separate, dated, read-only 24h non-performance verification protocol, **or** leave Kalshi stopped. This draft does not itself approve either choice, select dates, arm a workflow, or spend money.
