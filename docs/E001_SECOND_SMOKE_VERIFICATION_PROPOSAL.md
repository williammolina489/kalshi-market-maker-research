# Proposed E001 Infrastructure Smoke Verification V2 — Approval Required

**Draft prepared:** 2026-10-13  
**Current state:** OWNER APPROVED 2026-10-13 — RELEASE-BACKED READ-ONLY V2 READY FOR OCTOBER 14 ONE-TIME START WINDOW (NOT YET RUNNING)  
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


## Owner authorization and zero-paid-storage implementation (2026-10-14)

The owner authorized one new **24-hour, read-only, non-performance** Kalshi infrastructure verification on October 13, subject to no unverified billed capacity and preserving the original 30-day E001 safety gate.

### Billing evidence

Screenshots dated 2026-10-14 show GitHub Free, `321 / 2,000` included private-repository Actions minutes consumed, Actions billed usage `$0` after discounts, and `0 GB used / 0.5 GB included` as displayed in GitHub's billing-period storage meter. That meter does **not** prove physical storage of old Actions artifacts is zero; 576.10 MB of unexpired original smoke artifacts were verified separately via the original run's artifacts endpoint. Original evidence was NOT deleted or altered.

GitHub's published documentation says standard GitHub-hosted runners for a **public repository** are free, and GitHub Release assets are limited to **2 GiB per individual asset**, but have **no total-size or download-bandwidth limit**: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases . Actions/Packages shared artifact storage is NOT used by the new V2 workflow.

### Implemented transport

- The updated V2 workflow archives **all raw gzip segments AND all restart checkpoints** in a **draft GitHub Release** tied to the one authorization commit. It no longer contains either `actions/upload-artifact` or `actions/download-artifact`.
- Each raw gzip segment is verified against the collector's SHA-256 manifest before splitting into release parts no larger than **512 MiB**. All files are uploaded without `--clobber`. Restart checkpoints are packed with the runtime state, manifest, chunk summary and V2 authorization marker and are accompanied by SHA-256 checksums.
- Every subsequent runner verifies its checkpoint archive hash and member allowlist before resuming. Final review downloads every raw part, reconstructs and verifies each gzip digest, validates gzip framing, and performs the original hash-manifest + row-level immutable replay. Truncation, corruption, missing parts, expired data or conflicting release tags stop evidence collection/review without backfill.
- The transport is tested offline using a simulated GitHub Release service, including duplicate-asset and corrupted-checkpoint fail-closed scenarios. CI passes; no trading logic, performance analysis or live orders were added.
- GitHub `contents: write` scope is used solely by the gated V2 workflow to create/upload the evidence Release. Original experiment raw data remain untouched.

### One-time approved launch plan

- **Eligible date:** Wednesday 2026-10-14 after quote close; quote window reviewed is Thursday 2026-10-15 **09:00–15:30 America/New_York**.
- **Frozen V2 gate:** exact launch interval **2026-10-14 21:25:00Z to 22:25:00Z** (17:25–18:25 EDT); automatically checks 24h duration, frozen collector commit, public GET-only scope, no real-money/order/economic authorization, no Actions artifacts and a distinct marker.
- **Trigger:** the V2 workflow's GitHub Actions cron `37 21 14 10 *` (17:37 EDT on October 14). The authorization marker is staged by an explicit owner-approved Git commit in main before this time. A marker push outside the authorized window is safely skipped. If GitHub's scheduled start is delayed beyond 18:25 EDT, it stops with **no data collection** rather than shifting the window.
- **Evidence storage:** draft GitHub Release `kalshi-e001-v2-<authorization-commit-prefix>`, using public API responses only. No paid resources, sensitive trading credentials, or live execution.
- **Review:** integrity-only, performance-blinded, with original 99.5% orderbook gate unchanged. The official **30-day E001 evidence window remains unstarted**, even if this smoke finishes successfully.

This protocol does not claim that the 24-hour smoke is already running or that coverage will pass; the actual GitHub run ID and artifact checks must be verified after the scheduled trigger. Because real-world GitHub Actions scheduling and REST collection can have delays, the result can still be `INFRASTRUCTURE NOT VERIFIED` despite a syntactically successful workflow.

## Follow-through

After the V2 run starts, check that the first chunk has a live run ID and an owner-scoped draft Release. After the run finishes, download and replay all raw shards, verify intact manifests and report genuine scheduled-slot coverage. Do not launch another run or start official E001 evidence without another explicit owner decision.
