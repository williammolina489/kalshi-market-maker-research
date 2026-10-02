# E001 Infrastructure Smoke Protocol

This protocol is authorized for one 24-hour infrastructure run. It does not start the
30-day E001 evidence window and does not authorize economic-performance inspection.

## Runtime

The smoke is split across bounded GitHub Actions jobs because one hosted job cannot own
the full 24-hour wall-clock interval. A persisted smoke start/deadline, restart state,
trade watermark/dedup state, cumulative SHA-256 manifest, and immutable compressed JSONL
segments preserve continuity across chunk boundaries.

During the frozen 09:00-15:30 America/New_York quote window:

1. Fetch the current active KXHIGHNY markets and metadata at least every 30 seconds.
2. Fetch full returned books for every active market at 1 Hz using the public multi-market
   orderbook endpoint.
3. Poll public non-block trades at 1 Hz, following every returned pagination cursor before
   the next poll and retaining a durable watermark plus trade-ID dedup state.
4. Fetch exchange status every 5 seconds and incentive definitions every 60 seconds.
5. Record scheduled/request/receive timestamps, raw payloads, errors, collector commit,
   schema version, and content hashes. Missed slots are explicit gaps and are never backfilled.

Outside the quote window the workflow remains alive to preserve the fixed 24-hour
wall-clock smoke interval, but it does not invent quote-window observations.

## Integrity review

At the end, assemble the chunk artifacts and verify segment hashes, record hashes, UTC
normalization, monotonic source timestamps, cursor/watermark continuity, explicit gaps,
and raw-source counts. The review is infrastructure-only and remains marked
REVIEW_REQUIRED for human interpretation.

Smoke output must not contain gross or net strategy economics, strategy return, Sharpe,
drawdown, per-fill/contract economics, economic rankings, or an E001 economic PASS/FAIL.
The 30-day economic evaluator remains absent.
