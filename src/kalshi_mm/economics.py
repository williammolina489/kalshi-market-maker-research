"""Deterministic market-structure calculations used by preregistered research."""

from __future__ import annotations

from decimal import Decimal

from .models import BookLevel, DerivedTopOfBook

ONE = Decimal("1")


def derive_top_of_book(
    market_ticker: str,
    yes_bids: tuple[BookLevel, ...],
    no_bids: tuple[BookLevel, ...],
) -> DerivedTopOfBook:
    """Derive YES-scale bid/ask, midpoint, spread, and microprice.

    Kalshi REST order books expose YES bids and NO bids. A NO bid at n implies a YES ask at 1-n.
    """
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
        market_ticker=market_ticker,
        best_yes_bid=bid,
        best_yes_ask=ask,
        best_bid_size=best_yes.count,
        best_ask_size=best_no.count,
        midpoint=midpoint,
        spread=spread,
        microprice=microprice,
    )
