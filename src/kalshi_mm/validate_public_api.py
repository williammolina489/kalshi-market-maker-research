"""Read-only smoke test for Kalshi public REST data. Never sends a write request."""

from __future__ import annotations

import json

from .client import ReadOnlyKalshiClient
from .config import INITIAL_SERIES_TICKER


def main() -> None:
    client = ReadOnlyKalshiClient()
    status = client.get_exchange_status()
    series = client.get_series(INITIAL_SERIES_TICKER)
    markets = client.get_markets(series_ticker=INITIAL_SERIES_TICKER, status="open")
    incentives = client.get_incentives(status="active")

    market_rows = markets.get("markets", [])
    first_book = None
    if market_rows:
        ticker = market_rows[0]["ticker"]
        first_book = {"ticker": ticker, "book": client.get_orderbook(ticker, depth=5)}

    print(
        json.dumps(
            {
                "mode": "READ_ONLY_PUBLIC_REST",
                "exchange_status": status,
                "series": series,
                "open_market_count": len(market_rows),
                "active_incentive_count": len(incentives.get("incentive_programs", [])),
                "sample_orderbook": first_book,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
