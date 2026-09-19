# Architecture

## Design principle

Separate observation, valuation, quoting policy, risk, and any future execution capability so a research component cannot accidentally become a trading system.

```text
public market data
      |
      v
raw immutable observations  ---> provenance / integrity checks
      |
      v
derived book state / fair value
      |
      v
simulated quoting policy
      |
      v
simulated fill + inventory/risk engine
      |
      v
research metrics / experiment decision

[NO FUNDED EXECUTION ADAPTER]
```

## Modules today

- `kalshi_mm.client`: unauthenticated, read-only HTTP `GET` client for public endpoints.
- `kalshi_mm.models`: raw/derived observation types.
- `kalshi_mm.economics`: deterministic top-of-book and microprice calculations.
- `kalshi_mm.validate_public_api`: optional public-API smoke test; it cannot place or cancel orders.

## Prospective collector design

Raw records must be append-only and UTC timestamped. Recommended raw partitions:

- `raw/market_metadata/date=YYYY-MM-DD/*.jsonl.gz`
- `raw/orderbooks/date=YYYY-MM-DD/*.jsonl.gz`
- `raw/trades/date=YYYY-MM-DD/*.jsonl.gz`
- `raw/incentives/date=YYYY-MM-DD/*.jsonl.gz`
- `raw/exchange_status/date=YYYY-MM-DD/*.jsonl.gz`

Every record should carry:

- collector receive timestamp (UTC)
- source endpoint and request parameters
- source event/market/series ticker where relevant
- raw response payload or lossless normalized payload
- collector version / Git commit
- content hash
- pagination cursor or polling watermark where relevant
- data-quality flags

Derived analytics belong under a separate `derived/` namespace and must be reproducible from raw observations.

## Fail-closed rules

The research engine must not create a simulated quote when:

- market status is not active
- the book is missing, crossed, stale, or invalid
- required price-range metadata is missing
- settlement rules/source cannot be resolved
- current fee metadata is unresolved
- collector coverage is outside the preregistered window or fails integrity requirements

A future execution architecture, if ever approved, must additionally include a global kill switch, per-market and portfolio limits, stale-data detection, market-status validation, clock-skew detection, duplicate-order prevention, API-failure handling, cancel-all-on-integrity-failure behavior, and hard no-trading-after-close logic.
