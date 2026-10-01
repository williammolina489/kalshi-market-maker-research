"""Performance-blinded smoke-test reporting only."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class SmokeReport:
    book_samples: int = 0
    valid_books: int = 0
    eligible_opportunities: int = 0
    hypothetical_quotes: int = 0
    qualifying_trade_volume: Decimal = Decimal("0")
    hypothetical_fills: Decimal = Decimal("0")
    metadata_samples: int = 0
    integrity_errors: int = 0
    gaps: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "book_samples": self.book_samples,
            "valid_books": self.valid_books,
            "eligible_opportunities": self.eligible_opportunities,
            "hypothetical_quotes": self.hypothetical_quotes,
            "qualifying_trade_volume": str(self.qualifying_trade_volume),
            "hypothetical_fills": str(self.hypothetical_fills),
            "metadata_samples": self.metadata_samples,
            "integrity_errors": self.integrity_errors,
            "gaps": list(self.gaps),
        }
