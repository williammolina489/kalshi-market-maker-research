# API Contract Revalidation

Stage 0 live unauthenticated revalidation (orchestrator run `35790814838`) returned HTTP 200 without authorization headers for series, open markets, event, market, orderbook, trades, exchange status, incentive programs, and series/fee changes. This is the runtime evidence used by the collector; no credentials are added.

The first-party Get Market Orderbook reference currently renders authentication headers, which conflicts with that fresh production probe. The discrepancy is recorded rather than guessed away: this rebuild uses the observed public REST behavior and remains GET-only. If that behavior changes, collection fails closed.

Current contracts preserved by the raw envelope include:

- `orderbook_fp.yes_dollars` and `no_dollars`, retaining every returned `[price_dollars, count_fp]` level.
- Trade identity, ticker, `count_fp`, both price fields, `created_time`, block flag, taker book/outcome/side fields, cursor, and pagination lineage.
- Market status, close/expiration, rules, fixed-point values, and `price_ranges`; series fee and settlement fields; event fee overrides.
- Public, paginated incentive definitions including cursor and reward/target/date fields.

WebSockets are not used because authentication is required and is unnecessary for the frozen public REST cadence.
