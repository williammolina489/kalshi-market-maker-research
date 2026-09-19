from decimal import Decimal

import pytest

from kalshi_mm.economics import derive_top_of_book
from kalshi_mm.models import BookLevel


def test_derive_top_of_book_and_microprice() -> None:
    yes = (BookLevel(Decimal("0.40"), Decimal("30")),)
    no = (BookLevel(Decimal("0.55"), Decimal("10")),)

    top = derive_top_of_book("TEST", yes, no)

    assert top.best_yes_bid == Decimal("0.40")
    assert top.best_yes_ask == Decimal("0.45")
    assert top.spread == Decimal("0.05")
    assert top.midpoint == Decimal("0.425")
    assert top.microprice == Decimal("0.4375")


def test_locked_book_fails_closed() -> None:
    yes = (BookLevel(Decimal("0.50"), Decimal("10")),)
    no = (BookLevel(Decimal("0.50"), Decimal("10")),)

    with pytest.raises(ValueError, match="locked or crossed"):
        derive_top_of_book("TEST", yes, no)
