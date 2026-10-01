"""Append-only compressed JSONL storage with hash manifests and fail-closed replay."""

from __future__ import annotations

import gzip
import hashlib
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import COLLECTOR_SCHEMA_VERSION
from .models import IntegrityError


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    return value.astimezone(UTC).isoformat()


class AppendOnlyStore:
    def __init__(
        self,
        root: Path,
        *,
        segment_name: str = "observations.jsonl.gz",
        collector_commit: str = "unknown",
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.segment = self.root / segment_name
        self.manifest = self.root / "manifest.json"
        self.collector_commit = collector_commit

    def append(
        self,
        *,
        source: str,
        payload: dict[str, Any],
        scheduled_at: datetime | None = None,
        requested_at: datetime | None = None,
        received_at: datetime | None = None,
        endpoint: str = "",
        params: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> str:
        received = received_at or datetime.now(UTC)
        row: dict[str, Any] = {
            "schema_version": COLLECTOR_SCHEMA_VERSION,
            "collector_commit": self.collector_commit,
            "received_at_utc": _iso(received),
            "scheduled_at_utc": _iso(scheduled_at),
            "requested_at_utc": _iso(requested_at),
            "source": source,
            "endpoint": endpoint,
            "params": params or {},
            "payload": payload,
            "error": error,
        }
        content_hash = hashlib.sha256(_canonical(row)).hexdigest()
        row["content_sha256"] = content_hash
        with gzip.open(self.segment, "at", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        self._write_manifest()
        return content_hash

    def _write_manifest(self) -> None:
        digest = hashlib.sha256(self.segment.read_bytes()).hexdigest()
        manifest = {
            "schema_version": COLLECTOR_SCHEMA_VERSION,
            "segments": [{"path": self.segment.name, "sha256": digest}],
        }
        self.manifest.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")

    def replay(self) -> Iterator[dict[str, Any]]:
        if not self.manifest.exists():
            raise IntegrityError("manifest missing")
        try:
            manifest = json.loads(self.manifest.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise IntegrityError("manifest unreadable") from exc
        last_by_source: dict[str, datetime] = {}
        for entry in manifest.get("segments", []):
            path = self.root / entry["path"]
            if not path.exists():
                raise IntegrityError("segment missing")
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise IntegrityError("segment hash mismatch")
            try:
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    for line in handle:
                        row = json.loads(line)
                        observed_hash = row.pop("content_sha256", None)
                        expected_hash = hashlib.sha256(_canonical(row)).hexdigest()
                        if observed_hash != expected_hash:
                            raise IntegrityError("record hash mismatch")
                        row["content_sha256"] = observed_hash
                        received = datetime.fromisoformat(row["received_at_utc"])
                        source = str(row["source"])
                        prior = last_by_source.get(source)
                        if prior is not None and received < prior:
                            raise IntegrityError("non-monotonic source timestamp")
                        last_by_source[source] = received
                        yield row
            except IntegrityError:
                raise
            except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise IntegrityError("segment replay corruption") from exc
