# Data Sources

Last verified: 2026-09-19

## Authoritative Kalshi sources

- API documentation index: https://docs.kalshi.com/llms.txt
- Production REST: https://external-api.kalshi.com/trade-api/v2
- Demo REST: https://external-api.demo.kalshi.co/trade-api/v2
- Production WebSocket: wss://external-api-ws.kalshi.com/trade-api/ws/v2
- Demo WebSocket: wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2
- Fee schedule: https://kalshi.com/docs/kalshi-fee-schedule.pdf
- Liquidity incentive terms/help: https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program
- Member agreement: https://kalshi.com/docs/kalshi-member-agreement.pdf

## E001 public REST sources

Planned read-only inputs:

- `GET /series/KXHIGHNY`
- `GET /markets?series_ticker=KXHIGHNY&status=open`
- `GET /markets/{ticker}`
- `GET /markets/{ticker}/orderbook`
- `GET /markets/trades?ticker={ticker}&is_block_trade=false`
- `GET /incentive_programs`
- `GET /exchange/status`

If the multiple-orderbooks endpoint is confirmed stable in the collector implementation, prefer it to reduce request count while preserving per-market provenance.

## Historical-data limitation

Kalshi's documented historical API archives markets/candlesticks, trades, fills, orders, and positions. It does **not** document a historical full order-book endpoint. Therefore E001 queue/fill research must be built from prospective book capture; no historical L2 book may be fabricated from candles or later states.

## KXHIGHNY settlement source

Current series metadata identifies The Weather Company (`weather.com/kalshi`) as the settlement source and includes an explicit material-error/revision provision. The collector must persist the exact series metadata and market rules observed during the evidence window rather than relying on a generic weather-help article.

## Incentives

The public `GET /incentive_programs` response exposes market, program type, dates, reward amount, discount factor, target size, and payout state. Program rules can change and the overall regular-user program is scheduled to end 2027-01-01 unless modified earlier. Incentive estimates are kept separate from core market-making P/L.
