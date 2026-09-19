"""Lossless research-facing observation models."""

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
    source: Literal["rest", "websocket"]


@dataclass(frozen=True, slots=True)
class RawTrade:
    trade_id: str
    market_ticker: str
    created_at_utc: datetime
    count: Decimal
    yes_price: Decimal
    taker_book_side: Literal["bid", "ask"]
    is_block_trade: bool


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
