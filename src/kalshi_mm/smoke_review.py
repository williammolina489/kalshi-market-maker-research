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
