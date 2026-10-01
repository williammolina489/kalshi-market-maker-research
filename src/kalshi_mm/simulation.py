"""Conservative, performance-blinded hypothetical quote and inventory state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal

from .economics import MAX_REST_SECONDS, MIN_REST_SECONDS
from .models import RawTrade

Side = Literal["bid", "ask"]


@dataclass(slots=True)
class QuoteState:
    market_ticker: str
    side: Side
    price: Decimal
    remaining: Decimal
    queue_ahead: Decimal
    created_at: datetime
    last_observed_at: datetime
    active: bool = True
    filled: Decimal = Decimal("0")
    cancel_reason: str | None = None

    def observe_depth(self, displayed: Decimal, *, observed_at: datetime | None = None) -> None:
        if displayed < 0:
            raise ValueError("displayed depth must be non-negative")
        if observed_at is not None:
            self.last_observed_at = observed_at
        # Frozen queue rule: later depth disappearance/cancellation gets zero credit.

    def consume_trade(self, trade: RawTrade) -> Decimal:
        if not self.active or trade.is_block_trade or trade.market_ticker != self.market_ticker:
            return Decimal("0")
        if trade.yes_price != self.price or not _qualifying_side(self.side, trade):
            return Decimal("0")
        if trade.count <= 0:
            return Decimal("0")
        consumed = min(self.queue_ahead, trade.count)
        self.queue_ahead -= consumed
        excess = trade.count - consumed
        fill = min(self.remaining, max(Decimal("0"), excess))
        self.remaining -= fill
        self.filled += fill
        if self.remaining == 0:
            self.active = False
            self.cancel_reason = "filled"
        return fill

    def should_reprice(
        self,
        now: datetime,
        *,
        price: Decimal,
        fair_value: Decimal,
        prior_fair_value: Decimal,
        tick: Decimal,
        spread_ticks: int,
        eligible: bool,
    ) -> bool:
        age = (now - self.created_at).total_seconds()
        if not eligible or age >= MAX_REST_SECONDS:
            return True
        if age < MIN_REST_SECONDS:
            return False
        return (
            price != self.price
            or abs(fair_value - prior_fair_value) >= tick
            or spread_ticks < 3
        )

    def cancel(self, reason: str) -> None:
        self.active = False
        self.cancel_reason = reason


def _qualifying_side(side: Side, trade: RawTrade) -> bool:
    book_side = trade.taker_book_side.lower()
    if side == "bid":
        return book_side in {"ask", "offer"}
    return book_side == "bid"


@dataclass(slots=True)
class Inventory:
    positions: dict[str, Decimal] = field(default_factory=dict)
    per_market_limit: Decimal = Decimal("20.00")
    aggregate_limit: Decimal = Decimal("40.00")

    @property
    def aggregate_absolute(self) -> Decimal:
        return sum((abs(value) for value in self.positions.values()), Decimal("0"))

    def can_fill(self, ticker: str, signed_amount: Decimal) -> bool:
        current = self.positions.get(ticker, Decimal("0"))
        updated = current + signed_amount
        projected = self.aggregate_absolute - abs(current) + abs(updated)
        within_limits = abs(updated) <= self.per_market_limit and projected <= self.aggregate_limit
        if within_limits:
            return True
        risk_reducing = abs(updated) < abs(current) and projected < self.aggregate_absolute
        return risk_reducing

    def apply(self, ticker: str, signed_amount: Decimal) -> None:
        if not self.can_fill(ticker, signed_amount):
            raise ValueError("inventory limit")
        self.positions[ticker] = self.positions.get(ticker, Decimal("0")) + signed_amount


def initialize_quote(
    *,
    ticker: str,
    side: Side,
    price: Decimal,
    displayed_size: Decimal,
    now: datetime,
    size: Decimal = Decimal("10.00"),
) -> QuoteState:
    if displayed_size < 0 or size <= 0:
        raise ValueError("invalid quote size")
    return QuoteState(ticker, side, price, size, displayed_size, now, now)
