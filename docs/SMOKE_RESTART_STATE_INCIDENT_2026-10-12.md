# October 2026 — Kalshi E001 smoke restart-state incident

**Evidence:** Read-only inspection of immutable GitHub Actions run [36944108882](https://github.com/williammolina489/kalshi-market-maker-research/actions/runs/36944108882), artifacts `e001-smoke-integrity-review` and `e001-smoke-state-5`.

**No historic smoke evidence was rewritten, excluded, reconstructed, or backfilled. Economic performance remains unviewed.**

## Verified observations

- The 24-hour smoke completed at 2026-10-03 00:04 UTC. The review preserved `REVIEW_REQUIRED`, not integrity PASS.
- `cadence_gap_records`: **10,698**. Each such record can cover multiple actual missed scheduled slots.
- Final `restart.json` was **178,201,225 bytes** uncompressed.
- The only key in `seen_trade_ids` was `__global__`, containing **3,873,924 trade IDs**.
- The collector was polling unfiltered exchange-wide `/markets/trades` and storing **all** those IDs in persistent JSON state, despite the frozen `KXHIGHNY` research universe.
- That state was written every five seconds in the smoke runner. The huge repeated serialization and disk I/O created a material candidate cause of missed 1-Hz polls.
- The final artifact reports only one `trade_watermark` and no per-market trade cursors. The immutable raw requests and gap logs remain authoritative.

This diagnosis establishes an objective state-size defect. **It does not prove that it caused every gap**, that the new implementation reaches 99.5% coverage, or that a new test will pass.

## Preventive remediation (future runs only)

The read-only public API still returns its full raw trade pages and all pagination cursors continue to be traversed. The collector now:

1. Deduplicates persistent trade IDs only for ticker prefix `KXHIGHNY-`, matching the frozen series.
2. Continues to validate trade identity and pagination lineage, failing closed when market identity is missing.
3. Computes the global request watermark from **all** returned trade timestamps, including unrelated markets. This avoids repeatedly fetching exchange-wide history while the target market has no trades.
4. Retains complete raw response pages and original content hashes; it does not alter existing smoke files.

Tests exercise thousands of unrelated trade IDs, target duplicate handling, cursor gaps, missing-ticker failure, and watermark movement without a target trade.

The independently merged polling overlap and per-stream missed-slot accounting are in PRs #5 and #6.

## Governance

This is an infrastructure repair for a future explicitly authorized non-performance smoke. The old October 1 smoke authorization is spent. No new smoke, E001 30-day evidence run, economic analysis, or execution is authorized by this note.
