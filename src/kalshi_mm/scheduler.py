"""Restart-safe cadence state for bounded prospective collection chunks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(slots=True)
class RestartState:
    next_due: dict[str, str] = field(default_factory=dict)
    trade_cursor: str | None = None
    trade_watermark: str | None = None
    last_received: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> RestartState:
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text())
        return cls(
            next_due=dict(payload.get("next_due", {})),
            trade_cursor=payload.get("trade_cursor"),
            trade_watermark=payload.get("trade_watermark"),
            last_received=dict(payload.get("last_received", {})),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "next_due": self.next_due,
                    "trade_cursor": self.trade_cursor,
                    "trade_watermark": self.trade_watermark,
                    "last_received": self.last_received,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )


class CadenceScheduler:
    CADENCE_SECONDS = {
        "book": 1,
        "trades": 1,
        "metadata": 30,
        "exchange_status": 5,
        "incentives": 60,
    }

    def __init__(self, state: RestartState | None = None) -> None:
        self.state = state or RestartState()

    def set_next_due(self, stream: str, when: datetime) -> None:
        self._validate_stream(stream)
        self.state.next_due[stream] = self._utc_iso(when)

    def due_slots(self, stream: str, now: datetime) -> list[datetime]:
        self._validate_stream(stream)
        now_utc = now.astimezone(UTC)
        raw = self.state.next_due.get(stream)
        if raw is None:
            return []
        due = datetime.fromisoformat(raw).astimezone(UTC)
        slots: list[datetime] = []
        step = timedelta(seconds=self.CADENCE_SECONDS[stream])
        while due <= now_utc:
            slots.append(due)
            due += step
            if len(slots) > 100000:
                raise ValueError("unbounded cadence gap")
        self.state.next_due[stream] = due.isoformat()
        return slots

    def mark_received(self, stream: str, *, scheduled_at: datetime, received_at: datetime) -> None:
        self._validate_stream(stream)
        self.state.last_received[stream] = self._utc_iso(received_at)
        next_due = scheduled_at.astimezone(UTC) + timedelta(
            seconds=self.CADENCE_SECONDS[stream]
        )
        self.state.next_due[stream] = next_due.isoformat()

    def mark_trade_page(self, *, cursor: str | None, watermark: str | None) -> None:
        self.state.trade_cursor = cursor
        if watermark is not None:
            self.state.trade_watermark = watermark

    @staticmethod
    def _utc_iso(value: datetime) -> str:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone-aware datetime required")
        return value.astimezone(UTC).isoformat()

    def _validate_stream(self, stream: str) -> None:
        if stream not in self.CADENCE_SECONDS:
            raise KeyError(stream)
