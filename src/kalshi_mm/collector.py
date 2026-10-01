"""Read-only E001 prospective collector primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .client import ReadOnlyKalshiClient
from .config import INITIAL_SERIES_TICKER
from .scheduler import CadenceScheduler
from .storage import AppendOnlyStore


class TradeContinuityError(ValueError):
    """Raised when trade pagination lineage is incomplete or contradictory."""


@dataclass(slots=True)
class TradeContinuity:
    cursor: str | None = None
    seen_trade_ids: set[str] = field(default_factory=set)

    def accept_page(
        self,
        payload: dict[str, Any],
        *,
        requested_cursor: str | None,
    ) -> list[dict[str, Any]]:
        if self.cursor is not None and requested_cursor != self.cursor:
            raise TradeContinuityError("trade cursor lineage gap")
        if self.cursor is None and requested_cursor is not None:
            raise TradeContinuityError("unexpected initial trade cursor")
        trades = payload.get("trades")
        if not isinstance(trades, list):
            raise TradeContinuityError("malformed trades page")
        accepted: list[dict[str, Any]] = []
        for row in trades:
            trade_id = row.get("trade_id")
            if not isinstance(trade_id, str) or not trade_id:
                raise TradeContinuityError("trade without identity")
            if trade_id in self.seen_trade_ids:
                continue
            self.seen_trade_ids.add(trade_id)
            accepted.append(row)
        next_cursor = payload.get("cursor")
        if next_cursor is not None and not isinstance(next_cursor, str):
            raise TradeContinuityError("malformed next cursor")
        if requested_cursor is not None and next_cursor == requested_cursor and trades:
            raise TradeContinuityError("non-advancing trade cursor")
        self.cursor = next_cursor
        return accepted


class Collector:
    def __init__(
        self,
        client: ReadOnlyKalshiClient,
        store: AppendOnlyStore,
        scheduler: CadenceScheduler | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self.scheduler = scheduler or CadenceScheduler()
        self.trade_continuity = TradeContinuity(cursor=self.scheduler.state.trade_cursor)

    @staticmethod
    def _now(value: datetime | None) -> datetime:
        observed = value or datetime.now(UTC)
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError("timezone-aware datetime required")
        return observed.astimezone(UTC)

    def discover_markets(self, *, now: datetime | None = None) -> list[str]:
        observed = self._now(now)
        payload = self.client.get_markets(
            series_ticker=INITIAL_SERIES_TICKER,
            status="open",
            limit=100,
        )
        self.store.append(
            source="markets",
            payload=payload,
            received_at=observed,
            endpoint="/markets",
            params={"series_ticker": INITIAL_SERIES_TICKER, "status": "open", "limit": 100},
        )
        rows = payload.get("markets", [])
        return [
            row["ticker"]
            for row in rows
            if isinstance(row, dict)
            and isinstance(row.get("ticker"), str)
            and row.get("series_ticker", INITIAL_SERIES_TICKER) == INITIAL_SERIES_TICKER
        ]

    def collect_orderbook(self, ticker: str, *, now: datetime | None = None) -> dict[str, Any]:
        observed = self._now(now)
        payload = self.client.get_orderbook(ticker, depth=0)
        self.store.append(
            source="orderbook",
            payload=payload,
            received_at=observed,
            endpoint=f"/markets/{ticker}/orderbook",
            params={"ticker": ticker, "depth": 0},
        )
        return payload

    def collect_market_metadata(
        self, ticker: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        observed = self._now(now)
        payload = self.client.get_market(ticker)
        self.store.append(
            source="market_metadata",
            payload=payload,
            received_at=observed,
            endpoint=f"/markets/{ticker}",
            params={"ticker": ticker},
        )
        return payload

    def collect_exchange_status(self, *, now: datetime | None = None) -> dict[str, Any]:
        observed = self._now(now)
        payload = self.client.get_exchange_status()
        self.store.append(
            source="exchange_status",
            payload=payload,
            received_at=observed,
            endpoint="/exchange/status",
        )
        return payload

    def collect_incentives(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        observed = self._now(now)
        cursor: str | None = None
        pages: list[dict[str, Any]] = []
        seen_cursors: set[str] = set()
        while True:
            payload = self.client.get_incentives(status="active", limit=1000, cursor=cursor)
            self.store.append(
                source="incentives",
                payload=payload,
                received_at=observed,
                endpoint="/incentive_programs",
                params={"status": "active", "limit": 1000, "cursor": cursor},
            )
            pages.append(payload)
            next_cursor = payload.get("next_cursor") or payload.get("cursor")
            if not next_cursor:
                break
            if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
                raise ValueError("incentive pagination gap")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
        return pages

    def collect_trades(
        self,
        ticker: str,
        *,
        cursor: str | None = None,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        observed = self._now(now)
        requested_cursor = self.trade_continuity.cursor if cursor is None else cursor
        payload = self.client.get_trades(ticker=ticker, cursor=requested_cursor, limit=1000)
        rows = self.trade_continuity.accept_page(payload, requested_cursor=requested_cursor)
        self.store.append(
            source="trades",
            payload=payload,
            received_at=observed,
            endpoint="/markets/trades",
            params={"ticker": ticker, "cursor": requested_cursor, "limit": 1000},
        )
        watermark = str(rows[-1].get("created_time")) if rows else None
        self.scheduler.mark_trade_page(cursor=self.trade_continuity.cursor, watermark=watermark)
        return rows
