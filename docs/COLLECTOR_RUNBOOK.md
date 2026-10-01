# Collector Runbook

The collector is a read-only prospective observer for `KXHIGHNY`. It sends public HTTPS `GET` requests only. It does not place, amend, or cancel exchange orders and contains no credentials.

## Cadence

During 09:00-15:30 America/New_York, schedule full returned books per active market at 1 Hz, trades at 1 Hz with cursor/watermark continuity, metadata at least every 30 seconds and on lifecycle change, exchange status every 5 seconds, and incentives every 60 seconds. Use `zoneinfo`; do not hard-code UTC offsets. Preserve the full orderbook response, not only top-of-book.

## Bounded restarts

Run finite chunks appropriate to the host runtime. Before stopping, persist restart state containing each stream's next due time and the trade cursor/watermark. On restart, load that state, continue pagination from the persisted lineage, and append immutable raw observations. Never claim a missed slot was observed and never backfill it from a later response.

## Integrity and replay

Each compressed JSONL record includes scheduled/request/receive timestamps, endpoint and parameters, raw payload, schema/collector version, and a content hash. The manifest hashes each segment. Replay verifies both manifest and record hashes and fails closed on missing, truncated, malformed, decompression-corrupted, or non-monotonic source data.

## Safety

The smoke layer can report structural validity and hypothetical queue/inventory state only. It must not calculate or expose E001 economic performance. Do not run the manual smoke protocol or begin the 30-day E001 window until the project owner approves the relevant gate.
