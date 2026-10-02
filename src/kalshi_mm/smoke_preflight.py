"""Live read-only preflight for the authorized E001 smoke endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from .client import ReadOnlyKalshiClient
from .config import INITIAL_SERIES_TICKER


def main() -> None:
    client = ReadOnlyKalshiClient(timeout=15.0)
    markets = client.get_markets(
        series_ticker=INITIAL_SERIES_TICKER,
        status="open",
        limit=100,
    )
    rows = [row for row in markets.get("markets", []) if isinstance(row, dict)]
    active = sorted(
        {
            str(row["ticker"])
            for row in rows
            if row.get("status") == "active" and isinstance(row.get("ticker"), str)
        }
    )
    if not active:
        raise SystemExit("no active KXHIGHNY markets returned")

    books = client.get_orderbooks(active[:100])
    returned = {
        row.get("ticker")
        for row in books.get("orderbooks", [])
        if isinstance(row, dict)
    }
    missing = sorted(set(active[:100]) - returned)
    if missing:
        raise SystemExit(f"batch orderbook missing markets: {missing}")

    now = datetime.now(UTC)
    trades = client.get_trades(
        ticker=None,
        limit=10,
        min_ts=int((now - timedelta(minutes=1)).timestamp()),
    )
    if "trades" not in trades or "cursor" not in trades:
        raise SystemExit("trade response contract mismatch")

    status = client.get_exchange_status()
    if not isinstance(status, dict) or not status:
        raise SystemExit("exchange status response empty")

    series = client.get_series(INITIAL_SERIES_TICKER)
    if not isinstance(series, dict) or not series:
        raise SystemExit("series response empty")

    event_tickers = sorted(
        {
            str(row["event_ticker"])
            for row in rows
            if isinstance(row.get("event_ticker"), str)
        }
    )
    if event_tickers:
        event = client.get_event(event_tickers[0])
        if not isinstance(event, dict) or not event:
            raise SystemExit("event response empty")

    incentives = client.get_incentives(status="active", limit=1)
    if "incentive_programs" not in incentives:
        raise SystemExit("incentive response contract mismatch")

    print(
        json.dumps(
            {
                "mode": "READ_ONLY_UNAUTHENTICATED_SMOKE_PREFLIGHT",
                "active_market_count": len(active),
                "batch_orderbook_count": len(returned),
                "trade_contract_ok": True,
                "exchange_status_ok": True,
                "series_ok": True,
                "event_checked": bool(event_tickers),
                "incentives_ok": True,
                "write_requests_sent": False,
                "performance_metrics_computed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
