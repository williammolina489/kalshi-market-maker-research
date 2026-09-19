# Current Kalshi Environment Research

As of: 2026-09-19

This document records current operational facts from Kalshi first-party documentation. Re-verify before relying on any mutable rule.

## Access and eligibility

- Individual account eligibility: age 18+ and document verification when requested.
- Kalshi is available internationally but maintains a restricted-jurisdiction list in the Member Agreement. U.S. members must still ensure their use is lawful.
- For this project, access findings are informational only because real-money trading is prohibited.

Sources:
- https://help.kalshi.com/en/articles/13823778-signing-up-as-an-individual
- https://kalshi.com/docs/kalshi-member-agreement.pdf

## API surface

- Production REST: `https://external-api.kalshi.com/trade-api/v2`
- Demo REST: `https://external-api.demo.kalshi.co/trade-api/v2`
- Production WS: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
- Demo WS: `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2`
- Public REST market-data endpoints can be used without authentication.
- WebSocket handshakes currently require API-key authentication even for public market-data channels.
- Authenticated requests use `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP`, and RSA-PSS `KALSHI-ACCESS-SIGNATURE`; the signed message is timestamp + HTTP method + path without query parameters.

Sources:
- https://docs.kalshi.com/getting_started/api_environments
- https://docs.kalshi.com/getting_started/quick_start_market_data
- https://docs.kalshi.com/getting_started/api_keys
- https://docs.kalshi.com/getting_started/quick_start_websockets

## Market hierarchy and book format

Series are recurring templates, events are concrete real-world occurrences, and markets are binary outcomes inside events. `GET /markets/{ticker}/orderbook` exposes fixed-point YES and NO bid ladders. Asks are implied by the opposite-side bid. Fixed-point prices can have up to four decimal places; quantities support two decimal places and 0.01-contract granularity. Valid tick sizes are market-specific and must be read from `price_ranges`, not hardcoded.

Sources:
- https://docs.kalshi.com/getting_started/fixed_point_migration
- https://docs.kalshi.com/getting_started/orderbook_responses
- https://docs.kalshi.com/api-reference/market/get-market
- https://docs.kalshi.com/api-reference/market/get-market-orderbook

## Orders (documented, not implemented here)

The current event-market V2 create endpoint uses a single YES-price scale with `bid`/`ask`, fixed-point count/price, `good_till_canceled`, `fill_or_kill`, or `immediate_or_cancel` time-in-force, and fields including `post_only`, `cancel_order_on_pause`, and `reduce_only`. This project intentionally does not implement that endpoint.

Source: https://docs.kalshi.com/api-reference/orders/create-order-v2

## Rate limits

Authenticated API limits are token-bucket based with independent read/write budgets. Most requests default to 10 tokens; `GET /account/endpoint_costs` is authoritative for exceptions. Published event-contract budgets currently range from Basic 200 read / 100 write tokens per second through higher tiers. E001 will remain read-only and should minimize request volume regardless of allowance.

Source: https://docs.kalshi.com/getting_started/rate_limits

## Trading hours and closures

Kalshi currently advertises 24/7 trading except scheduled maintenance every Thursday from 03:00-05:00 ET. During the regular trading pause, placing/amending is disabled but cancellation remains available; a rare full exchange pause can also block cancellation. At market `close_time`, order operations are rejected and resting orders are subsequently cancelled.

Sources:
- https://help.kalshi.com/en/articles/13823807-what-are-trading-hours
- https://docs.kalshi.com/getting_started/maintenance_and_pauses
- https://docs.kalshi.com/getting_started/market_lifecycle

## Settlement

Simple binary YES resolves to $1 for YES holders and NO resolves to $1 for NO holders; only net positions settle. Settlement timing varies by market/data-source/manual review. Simple yes/no determinations have zero settlement fee, while sub-cent scalar settlement can have special handling.

Source: https://docs.kalshi.com/getting_started/market_settlement

## Fees

Current general event-contract formulas (fee schedule effective 2026-07-07):

- taker: `round_up(M * 0.07 * C * P * (1-P))`, default `M=1`
- maker: `round_up(M * 0.0175 * C * P * (1-P))`, default `M=0` unless the product is listed otherwise

Maker fees are only charged if the resting order ultimately executes. Event-level fee overrides and series fee changes can occur; E001 must therefore capture contemporaneous fee metadata rather than assuming zero maker fees forever. `KXHIGHNY` is not listed among the current non-standard fee series in the July 7 schedule, but that can change.

Sources:
- https://kalshi.com/docs/kalshi-fee-schedule.pdf
- https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes
- https://docs.kalshi.com/api-reference/events/get-event-fee-changes

## Liquidity incentives

Kalshi currently has a regular-user Liquidity Incentive Program through 2027-01-01 unless modified or ended earlier. Most regular U.S. members can participate; international/non-U.S. users, Kalshi affiliates/employees, and IB/FCM customers are excluded. Scoring samples resting orders once per second at a random point within each second and depends on size, distance from a reference price, target size, discount factor, and two-sided qualifying depth. Public API definitions expose program market, dates, reward, discount factor, and target size.

A separate designated Liquidity Provider / Market Maker framework exists for approved participants and can include reduced fees or adjusted position limits. E001 assumes no designated-market-maker status and must not mix those benefits into ordinary-user economics.

Sources:
- https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program
- https://docs.kalshi.com/api-reference/incentive-programs/get-incentives
- https://help.kalshi.com/en/articles/13823819-how-to-become-a-market-maker-on-kalshi

## Historical data

Official historical endpoints cover archived markets/candlesticks, trades, fills, orders, and positions; they do not document historical full order-book snapshots. That is the critical reason E001 must collect book depth prospectively.

Source: https://docs.kalshi.com/getting_started/historical_data

## Chosen initial research universe

`KXHIGHNY` only.

Reasons:

1. Daily recurring standardized structure.
2. Objective settlement metadata exposed by the API.
3. Current series metadata names The Weather Company as settlement source.
4. Public API quick-start itself uses KXHIGHNY as a market-data example.
5. Public Kalshi pages currently show repeated bucket markets and meaningful event activity, giving a reasonable basis to collect prospectively without selecting on historical strategy returns.
6. Restricting to one series reduces confounding from heterogeneous settlement rules and fee structures.

Important current-source change: a generic weather help article may describe older/other daily-weather settlement conventions, but current `KXHIGHNY` series metadata explicitly names The Weather Company and includes a material-error provision. The series/market metadata observed during E001 is authoritative for this experiment.
