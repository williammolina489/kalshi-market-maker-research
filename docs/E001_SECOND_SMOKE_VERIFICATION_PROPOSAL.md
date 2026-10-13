# Proposed E001 Infrastructure Smoke Verification V2 — Approval Required

**Draft prepared:** 2026-10-13  
**Current state:** OWNER APPROVED IN PRINCIPLE 2026-10-13 — LAUNCH BLOCKED PENDING VERIFIED STORAGE; NOT SCHEDULED OR RUNNING  
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


## Owner approval and explicit storage blocker (2026-10-13)

The project owner approved **one additional read-only, 24-hour Kalshi infrastructure smoke**, conditioned on storage checks; no 30-day E001 window or paid capacity was approved.

At inspection on October 13, the prior run still retained **576.10 MB** of GitHub Actions artifacts, including approximately **428.5 MB** of raw source segments. Free GitHub accounts include **500 MB** of shared Actions/Packages artifact storage; GitHub Pro includes **1 GB**. The connected GitHub API does not expose the owner's remaining account-wide free artifact capacity or any billing cap. A near-complete 23,400-slot quote session can generate materially more raw market data than the original ~10,597-book-batch test.

**Do not launch or commit the trigger marker yet.** The new CI-tested workflow `.github/workflows/e001-24h-verification-v2.yml` is installed only on this draft branch; its trigger is a separate **currently absent** `research/E001_VERIFICATION_V2_AUTHORIZATION.json` file, not the spent October 1 smoke marker. A new marker may be created only after GitHub account Billing confirms at least **1.5 GiB additional unallocated artifact storage**, a recent timestamp, and zero paid-capacity authorization. If that capacity is unavailable, keep this experiment stopped and consider a separately approved storage architecture instead of charging the user.

The marker must conform to `research/E001_VERIFICATION_V2_AUTHORIZATION_SCHEMA.json`. Its `collector_commit_sha` must pin the approved V2 implementation **before** the marker is committed to `main`; the launch gate checks that only the authorization file changed between that frozen commit and the launch SHA. A narrow predeclared evening New York launch interval is required so the ensuing exact 24-hour observer window includes the next complete 09:00–15:30 ET quote session.

The gate blocks stale confirmation, insufficient verified free storage, unauthenticated/restricted flags, a widened launch window, changed code, missing marker, and any attempt to reuse the old smoke authorization. Raw/state artifacts have **two-day retention**, with the final integrity-only review retained for three days. Those retention settings do not prove that enough quota is available; the owner must explicitly inspect/download the immutable evidence before expiry.

**Implementation is staged but NOT RUNNING**: no v2 marker has been created, no 24-hour job has started, and no performance data or orders have been accessed.

## Decision needed

The owner may choose to approve the preparation of a separate, dated, read-only 24h non-performance verification protocol, **or** leave Kalshi stopped. This draft does not itself approve either choice, select dates, arm a workflow, or spend money.
