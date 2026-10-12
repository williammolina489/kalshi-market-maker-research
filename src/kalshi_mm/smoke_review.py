"""Integrity-only review for the E001 infrastructure smoke artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .storage import AppendOnlyStore


def review(root: Path) -> dict[str, object]:
    runtime_path = root / "smoke_runtime.json"
    if not runtime_path.exists():
        raise ValueError("smoke runtime state missing")
    runtime = json.loads(runtime_path.read_text())
    counts: Counter[str] = Counter()
    errors = 0
    gap_records = 0
    missing_slots_by_stream: Counter[str] = Counter()
    successful_poll_slots: dict[str, set[str]] = {
        key: set() for key in ("book", "trades", "metadata", "exchange_status", "incentives")
    }
    attempted_poll_slots: dict[str, set[str]] = {
        key: set() for key in successful_poll_slots
    }
    stream_sources = {
        "orderbooks_batch": "book",
        "trades_global": "trades",
        "markets": "metadata",
        "exchange_status": "exchange_status",
        "incentives": "incentives",
    }
    first_received: datetime | None = None
    last_received: datetime | None = None

    store = AppendOnlyStore(root)
    for row in store.replay():
        source = str(row["source"])
        counts[source] += 1
        if row.get("error"):
            errors += 1
        if source == "cadence_gap":
            gap_records += 1
            gap_stream = row.get("payload", {}).get("stream")
            count = row.get("payload", {}).get("missing_count")
            if gap_stream not in attempted_poll_slots or type(count) is not int or count < 1:
                raise ValueError("invalid cadence-gap attribution in smoke evidence")
            missing_slots_by_stream[gap_stream] += count
        poll_stream = stream_sources.get(source)
        scheduled = row.get("scheduled_at_utc")
        if poll_stream is not None and scheduled is not None:
            attempted_poll_slots[poll_stream].add(str(scheduled))
            if not row.get("error"):
                successful_poll_slots[poll_stream].add(str(scheduled))
        received = datetime.fromisoformat(str(row["received_at_utc"])).astimezone(UTC)
        first_received = received if first_received is None else min(first_received, received)
        last_received = received if last_received is None else max(last_received, received)

    deadline = datetime.fromisoformat(str(runtime["deadline_utc"])).astimezone(UTC)
    now = datetime.now(UTC)
    summary: dict[str, object] = {
        "smoke_id": runtime["smoke_id"],
        "started_at_utc": runtime["started_at_utc"],
        "deadline_utc": runtime["deadline_utc"],
        "reviewed_at_utc": now.isoformat(),
        "wall_clock_window_complete": now >= deadline,
        "record_count_by_source": dict(sorted(counts.items())),
        "records_with_errors": errors,
        "cadence_gap_records": gap_records,
        # Gap *records* can each represent many missed polling slots. Report
        # distinct scheduled poll opportunities separately from pagination pages.
        "missing_scheduled_slots_by_stream": dict(sorted(missing_slots_by_stream.items())),
        "attempted_scheduled_slots_by_stream": {
            stream: len(slots) for stream, slots in attempted_poll_slots.items()
        },
        "successful_scheduled_slots_by_stream": {
            stream: len(slots) for stream, slots in successful_poll_slots.items()
        },
        "first_received_at_utc": first_received.isoformat() if first_received else None,
        "last_received_at_utc": last_received.isoformat() if last_received else None,
        "performance_blinded": True,
        "integrity_review_status": "REVIEW_REQUIRED",
    }
    (root / "smoke-review.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    summary = review(args.root)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
