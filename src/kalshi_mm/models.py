"""Typed, lossless models for public observations and derived smoke state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class RawObservationEnvelope:
    observed_at_utc: datetime
    source: str
    payload: dict[str, Any]
    git_commit: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class BookLevel:
    price: Decimal
    count: Decimal


@dataclass(frozen=True, slots=True)
class RawOrderBookSnapshot:
    observed_at_utc: datetime
    market_ticker: str
    yes_bids: tuple[BookLevel, ...]
    no_bids: tuple[BookLevel, ...]
    source: Literal["rest", "websocket"] = "rest"


@dataclass(frozen=True, slots=True)
class RawTrade:
    trade_id: str
    market_ticker: str
    created_at_utc: datetime
    count: Decimal
    yes_price: Decimal
    taker_book_side: str
    is_block_trade: bool
    no_price: Decimal | None = None
    taker_outcome_side: str | None = None
    taker_side: str | None = None


@dataclass(frozen=True, slots=True)
class DerivedTopOfBook:
    market_ticker: str
    best_yes_bid: Decimal
    best_yes_ask: Decimal
    best_bid_size: Decimal
    best_ask_size: Decimal
    midpoint: Decimal
    spread: Decimal
    microprice: Decimal


@dataclass(frozen=True, slots=True)
class PriceRange:
    start: Decimal
    end: Decimal
    tick_size: Decimal


@dataclass(frozen=True, slots=True)
class MarketMetadata:
    ticker: str
    status: str
    close_time: datetime
    expiration_time: datetime | None
    price_ranges: tuple[PriceRange, ...]
    rules_primary: Any
    rules_secondary: Any
    fee_metadata: Any
    settlement_sources: Any


class IntegrityError(ValueError):
    """Raised when an immutable segment or replay stream is not trustworthy."""
