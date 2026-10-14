# Project State

Last updated: 2026-10-14

## Status

FOUNDATION COMPLETE / V2 RELEASE-BACKED VERIFICATION OWNER-APPROVED / ONE-TIME LAUNCH OCT 14 17:37 EDT PENDING / E001 PREREGISTERED / PERFORMANCE UNVIEWED / 30D NOT RUNNING

The clean replacement collector is **REBUILT FROM CANONICAL E001 SPECIFICATION**.
The exact prior implementation was lost; the rebuild is not an exact recovery.

## Frozen safety boundary

- No live orders, funded execution, or real money.
- No trading credentials or authenticated order client.
- Public HTTPS GET observation only.
- Original non-performance 24-hour smoke authorized 2026-10-01; it is complete, its authorization spent.\n- Owner approved one separate 24-hour public-data-only verification on 2026-10-13. GitHub Release storage substitution is CI-verified and free of Actions artifact usage; prospective window on Oct 14 is being armed, not yet running.
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

## Approved second smoke, release-backed, launch pending

Owner approved one new 24-hour, performance-blinded, **public HTTPS GET only** infrastructure verification on 2026-10-13, conditioned on avoiding unverified paid resources. Billing screenshots on 2026-10-14 confirmed GitHub Free, 321/2000 included private-runner minutes consumed, Actions billable spend $0, and Actions storage billed as 0/0.5 GB. The first smoke's old ~576.10 MB of evidence artifacts are still present and unchanged.

PR #8 established fail-closed launch/time/trading restrictions. PR #9 merged on 2026-10-14 as `c77a462b84560c20c4dafb0ba960b11afa741119`, replacing ALL V2 Actions artifacts with GitHub draft Release assets. Each raw segment is split to max 512 MiB and SHA-verified; restart checkpoints and immutable hashes are also stored in Release assets. Offline simulated-GitHub tests reconstructed and verified five segments, rejected duplicates and detected corruption. CI and public GET preflight passed. No paid capacity, execution APIs, strategies or frozen experiment rules changed.

The distinct V2 authorization marker is to be added ONLY after main is frozen and verified. The planned one-time launch cron is **2026-10-14 21:37 UTC (17:37 EDT)**, with accepted start interval **21:25–22:25 UTC**. This allows an untouched full October 15, 2026 **09:00–15:30 ET** quote session inside the 24-hour observation window. GitHub Actions may delay cron; if it misses the approved hour the collector must NOT start or shift dates. Raw and restart data stay in the separate draft GitHub Release; this does not reuse the October 1 marker.

The first smoke remains REVIEW_REQUIRED with 10,698 legitimate cadence-gap records. Even successful V2 collection does not authorize the E001 30-day official window. Review actual missing 1-Hz slots and manifest replay without viewing economic data.

See `docs/E001_SECOND_SMOKE_VERIFICATION_PROPOSAL.md` and `research/E001_VERIFICATION_V2_AUTHORIZATION_SCHEMA.json` for frozen V2 conditions.

## Next permitted actions

1. Commit a single distinct owner-authorized V2 launch marker pinned to this frozen main SHA. Do not modify original E001 authorization.
2. At Oct 14 17:37 EDT, inspect the actual GitHub run: it must pass gate/preflight, create draft Release, and begin only public GET observations. Otherwise leave stopped and report no launch.
3. After at least 24h, independently verify all five raw segments, row checksums, source slot counts and 99.5% book gate, with zero backfill or economic analysis.
4. A separate later owner decision is required for an official 30-day E001 start; real trading is not authorized.

Until then E001 stays PREREGISTERED / NOT RUNNING. Do not calculate strategy P/L, fill economics or promotion metrics.
