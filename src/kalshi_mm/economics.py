"""Frozen E001 market-structure and eligibility calculations."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from .models import BookLevel, DerivedTopOfBook, PriceRange, RawOrderBookSnapshot

ONE = Decimal("1")
ET = ZoneInfo("America/New_York")
QUOTE_START = time(9, 0)
QUOTE_END = time(15, 30)
MIN_QUOTE_SIZE = Decimal("10.00")
MIN_REST_SECONDS = 30
MAX_REST_SECONDS = 300
MIN_CLOSE_SECONDS = 3600


def derive_top_of_book(
    market_ticker: str,
    yes_bids: tuple[BookLevel, ...],
    no_bids: tuple[BookLevel, ...],
) -> DerivedTopOfBook:
    if not yes_bids or not no_bids:
        raise ValueError("two-sided book required")
    best_yes = max(yes_bids, key=lambda level: level.price)
    best_no = max(no_bids, key=lambda level: level.price)
    ask = ONE - best_no.price
    bid = best_yes.price
    if bid >= ask:
        raise ValueError("book is locked or crossed")
    if best_yes.count <= 0 or best_no.count <= 0:
        raise ValueError("top-of-book sizes must be positive")
    spread = ask - bid
    midpoint = (bid + ask) / Decimal("2")
    microprice = (ask * best_yes.count + bid * best_no.count) / (
        best_yes.count + best_no.count
    )
    return DerivedTopOfBook(
        market_ticker,
        bid,
        ask,
        best_yes.count,
        best_no.count,
        midpoint,
        spread,
        microprice,
    )


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")


def in_quote_window(timestamp: datetime) -> bool:
    _require_aware(timestamp)
    local = timestamp.astimezone(ET)
    return QUOTE_START <= local.time().replace(tzinfo=None) <= QUOTE_END


def resolve_tick(price: Decimal, ranges: tuple[PriceRange, ...]) -> Decimal:
    for item in ranges:
        if item.start <= price <= item.end:
            if item.tick_size <= 0:
                raise ValueError("tick size must be positive")
            return item.tick_size
    raise ValueError("price is outside price_ranges")


def is_on_tick(price: Decimal, ranges: tuple[PriceRange, ...]) -> bool:
    try:
        for item in ranges:
            if item.start <= price <= item.end:
                if item.tick_size <= 0:
                    return False
                return (price - item.start) % item.tick_size == 0
    except ArithmeticError:
        return False
    return False


def spread_ticks(top: DerivedTopOfBook, ranges: tuple[PriceRange, ...]) -> int:
    if not is_on_tick(top.best_yes_bid, ranges) or not is_on_tick(top.best_yes_ask, ranges):
        raise ValueError("top prices are off tick")
    ticks = 0
    price = top.best_yes_bid
    while price < top.best_yes_ask:
        tick = resolve_tick(price, ranges)
        next_price = price + tick
        if next_price > top.best_yes_ask:
            raise ValueError("spread is not aligned to local ticks")
        price = next_price
        ticks += 1
        if ticks > 1000:
            raise ValueError("unreasonable tick traversal")
    return ticks


def eligible_for_quote(
    *,
    status: str,
    timestamp: datetime,
    close_time: datetime,
    top: DerivedTopOfBook,
    price_ranges: tuple[PriceRange, ...],
    fees_resolved: bool,
    rules_resolved: bool,
    paused: bool = False,
    integrity_ok: bool = True,
) -> bool:
    _require_aware(timestamp)
    _require_aware(close_time)
    if status != "active" or paused or not integrity_ok or not in_quote_window(timestamp):
        return False
    if (close_time - timestamp).total_seconds() < MIN_CLOSE_SECONDS:
        return False
    if top.best_bid_size < MIN_QUOTE_SIZE or top.best_ask_size < MIN_QUOTE_SIZE:
        return False
    if not is_on_tick(top.best_yes_bid, price_ranges):
        return False
    if not is_on_tick(top.best_yes_ask, price_ranges):
        return False
    try:
        if spread_ticks(top, price_ranges) < 3:
            return False
        bid_tick = resolve_tick(top.best_yes_bid, price_ranges)
        ask_tick = resolve_tick(top.best_yes_ask, price_ranges)
    except ValueError:
        return False
    if top.microprice < top.best_yes_bid + bid_tick:
        return False
    if top.microprice > top.best_yes_ask - ask_tick:
        return False
    return fees_resolved and rules_resolved


def parse_book(
    payload: dict,
    *,
    observed_at_utc: datetime,
    market_ticker: str,
) -> RawOrderBookSnapshot:
    _require_aware(observed_at_utc)
    book = payload.get("orderbook_fp", payload.get("orderbook", payload))
    yes_raw = book.get("yes_dollars")
    no_raw = book.get("no_dollars")
    if not isinstance(yes_raw, list) or not isinstance(no_raw, list) or not yes_raw or not no_raw:
        raise ValueError("complete YES/NO depth required")
    try:
        yes = tuple(BookLevel(Decimal(str(level[0])), Decimal(str(level[1]))) for level in yes_raw)
        no = tuple(BookLevel(Decimal(str(level[0])), Decimal(str(level[1]))) for level in no_raw)
    except (IndexError, TypeError, ArithmeticError) as exc:
        raise ValueError("malformed orderbook level") from exc
    if any(level.count <= 0 for level in (*yes, *no)):
        raise ValueError("book depth must be positive")
    return RawOrderBookSnapshot(observed_at_utc, market_ticker, yes, no)
