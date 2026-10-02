"""Bounded, restart-safe runner for the authorized E001 infrastructure smoke."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from datetime import time as wall_time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .client import ReadOnlyKalshiClient
from .collector import TradeContinuity, TradeContinuityError
from .config import INITIAL_SERIES_TICKER
from .economics import in_quote_window
from .scheduler import CadenceScheduler, RestartState
from .storage import AppendOnlyStore

ET = ZoneInfo("America/New_York")
STREAMS = ("book", "trades", "metadata", "exchange_status", "incentives")


@dataclass(slots=True)
class SmokeRuntimeState:
    smoke_id: str
    started_at_utc: str
    deadline_utc: str
    active_markets: list[str] = field(default_factory=list)
    event_tickers: list[str] = field(default_factory=list)
    chunks_completed: list[int] = field(default_factory=list)

    @classmethod
    def load_or_create(cls, path: Path, now: datetime) -> SmokeRuntimeState:
        if path.exists():
            payload = json.loads(path.read_text())
            return cls(
                smoke_id=str(payload["smoke_id"]),
                started_at_utc=str(payload["started_at_utc"]),
                deadline_utc=str(payload["deadline_utc"]),
                active_markets=list(payload.get("active_markets", [])),
                event_tickers=list(payload.get("event_tickers", [])),
                chunks_completed=list(payload.get("chunks_completed", [])),
            )
        smoke_id = now.strftime("e001-smoke-%Y%m%dT%H%M%SZ")
        return cls(
            smoke_id=smoke_id,
            started_at_utc=now.isoformat(),
            deadline_utc=(now + timedelta(hours=24)).isoformat(),
        )

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), sort_keys=True, indent=2) + "\n")


def next_quote_start(now: datetime) -> datetime:
    local = now.astimezone(ET)
    candidate = datetime.combine(local.date(), wall_time(9, 0), tzinfo=ET)
    if local >= candidate:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


def _record_gap(
    store: AppendOnlyStore,
    *,
    stream: str,
    slots: list[datetime],
    received_at: datetime,
) -> None:
    if len(slots) <= 1:
        return
    missing = slots[:-1]
    store.append(
        source="cadence_gap",
        payload={
            "stream": stream,
            "missing_count": len(missing),
            "first_missing_utc": missing[0].isoformat(),
            "last_missing_utc": missing[-1].isoformat(),
        },
        scheduled_at=missing[0],
        received_at=received_at,
        error="missed_scheduled_slots",
        update_manifest=False,
    )


def _latest_due(
    scheduler: CadenceScheduler,
    store: AppendOnlyStore,
    stream: str,
    now: datetime,
) -> datetime | None:
    slots = scheduler.due_slots(stream, now)
    if not slots:
        return None
    _record_gap(store, stream=stream, slots=slots, received_at=now)
    return slots[-1]


def _append_error(
    store: AppendOnlyStore,
    *,
    source: str,
    endpoint: str,
    params: dict[str, Any],
    scheduled_at: datetime,
    requested_at: datetime,
    exc: Exception,
) -> None:
    store.append(
        source=source,
        payload={},
        scheduled_at=scheduled_at,
        requested_at=requested_at,
        received_at=datetime.now(UTC),
        endpoint=endpoint,
        params=params,
        error=f"{type(exc).__name__}: {exc}",
        update_manifest=False,
    )


def _collect_metadata(
    client: ReadOnlyKalshiClient,
    store: AppendOnlyStore,
    runtime: SmokeRuntimeState,
    scheduled_at: datetime,
) -> None:
    requested = datetime.now(UTC)
    payload = client.get_markets(
        series_ticker=INITIAL_SERIES_TICKER,
        status="open",
        limit=100,
    )
    received = datetime.now(UTC)
    store.append(
        source="markets",
        payload=payload,
        scheduled_at=scheduled_at,
        requested_at=requested,
        received_at=received,
        endpoint="/markets",
        params={"series_ticker": INITIAL_SERIES_TICKER, "status": "open", "limit": 100},
        update_manifest=False,
    )
    rows = [row for row in payload.get("markets", []) if isinstance(row, dict)]
    runtime.active_markets = sorted(
        {
            str(row["ticker"])
            for row in rows
            if row.get("status") == "active" and isinstance(row.get("ticker"), str)
        }
    )
    runtime.event_tickers = sorted(
        {
            str(row["event_ticker"])
            for row in rows
            if isinstance(row.get("event_ticker"), str)
        }
    )

    requested = datetime.now(UTC)
    series = client.get_series(INITIAL_SERIES_TICKER)
    store.append(
        source="series_metadata",
        payload=series,
        scheduled_at=scheduled_at,
        requested_at=requested,
        received_at=datetime.now(UTC),
        endpoint=f"/series/{INITIAL_SERIES_TICKER}",
        params={"ticker": INITIAL_SERIES_TICKER},
        update_manifest=False,
    )
    for event_ticker in runtime.event_tickers:
        requested = datetime.now(UTC)
        event = client.get_event(event_ticker)
        store.append(
            source=f"event_metadata:{event_ticker}",
            payload=event,
            scheduled_at=scheduled_at,
            requested_at=requested,
            received_at=datetime.now(UTC),
            endpoint=f"/events/{event_ticker}",
            params={"event_ticker": event_ticker},
            update_manifest=False,
        )


def _collect_books(
    client: ReadOnlyKalshiClient,
    store: AppendOnlyStore,
    runtime: SmokeRuntimeState,
    scheduled_at: datetime,
) -> None:
    if not runtime.active_markets:
        store.append(
            source="orderbooks_batch",
            payload={"orderbooks": []},
            scheduled_at=scheduled_at,
            received_at=datetime.now(UTC),
            endpoint="/markets/orderbooks",
            params={"tickers": []},
            error="no_active_markets",
            update_manifest=False,
        )
        return
    requested = datetime.now(UTC)
    payload = client.get_orderbooks(runtime.active_markets)
    received = datetime.now(UTC)
    returned = {
        row.get("ticker")
        for row in payload.get("orderbooks", [])
        if isinstance(row, dict)
    }
    missing = sorted(set(runtime.active_markets) - returned)
    store.append(
        source="orderbooks_batch",
        payload=payload,
        scheduled_at=scheduled_at,
        requested_at=requested,
        received_at=received,
        endpoint="/markets/orderbooks",
        params={"tickers": runtime.active_markets},
        error=f"missing_orderbooks:{','.join(missing)}" if missing else None,
        update_manifest=False,
    )


def _parse_created_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _collect_trades(
    client: ReadOnlyKalshiClient,
    store: AppendOnlyStore,
    scheduler: CadenceScheduler,
    scheduled_at: datetime,
) -> None:
    seen = set(scheduler.state.seen_trade_ids.get("__global__", []))
    continuity = TradeContinuity(
        cursor=scheduler.state.trade_cursor,
        seen_trade_ids=seen,
    )
    watermark = _parse_created_time(scheduler.state.trade_watermark)
    min_ts = int(watermark.timestamp()) - 1 if watermark else int(scheduled_at.timestamp()) - 2
    newest = watermark

    while True:
        requested_cursor = continuity.cursor
        requested = datetime.now(UTC)
        payload = client.get_trades(
            ticker=None,
            limit=1000,
            cursor=requested_cursor,
            min_ts=min_ts,
        )
        received = datetime.now(UTC)
        rows = continuity.accept_page(payload, requested_cursor=requested_cursor)
        store.append(
            source="trades_global",
            payload=payload,
            scheduled_at=scheduled_at,
            requested_at=requested,
            received_at=received,
            endpoint="/markets/trades",
            params={
                "ticker": None,
                "cursor": requested_cursor,
                "limit": 1000,
                "min_ts": min_ts,
                "is_block_trade": False,
            },
            update_manifest=False,
        )
        for row in rows:
            created = _parse_created_time(row.get("created_time"))
            if created is not None and (newest is None or created > newest):
                newest = created
        scheduler.state.trade_cursor = continuity.cursor
        scheduler.state.seen_trade_ids["__global__"] = sorted(continuity.seen_trade_ids)
        if newest is not None:
            scheduler.state.trade_watermark = newest.isoformat()
        if continuity.cursor is None:
            break


def _collect_exchange_status(
    client: ReadOnlyKalshiClient,
    store: AppendOnlyStore,
    scheduled_at: datetime,
) -> None:
    requested = datetime.now(UTC)
    payload = client.get_exchange_status()
    store.append(
        source="exchange_status",
        payload=payload,
        scheduled_at=scheduled_at,
        requested_at=requested,
        received_at=datetime.now(UTC),
        endpoint="/exchange/status",
        update_manifest=False,
    )


def _collect_incentives(
    client: ReadOnlyKalshiClient,
    store: AppendOnlyStore,
    scheduled_at: datetime,
) -> None:
    cursor: str | None = None
    seen_cursors: set[str] = set()
    while True:
        requested = datetime.now(UTC)
        payload = client.get_incentives(status="active", limit=1000, cursor=cursor)
        store.append(
            source="incentives",
            payload=payload,
            scheduled_at=scheduled_at,
            requested_at=requested,
            received_at=datetime.now(UTC),
            endpoint="/incentive_programs",
            params={"status": "active", "limit": 1000, "cursor": cursor},
            update_manifest=False,
        )
        next_cursor = payload.get("next_cursor") or payload.get("cursor")
        if not next_cursor:
            break
        if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
            raise ValueError("incentive pagination gap")
        seen_cursors.add(next_cursor)
        cursor = next_cursor


def _initialize_due_times(scheduler: CadenceScheduler, now: datetime) -> None:
    first_due = now.replace(microsecond=0) if in_quote_window(now) else next_quote_start(now)
    for stream in STREAMS:
        if stream not in scheduler.state.next_due:
            scheduler.set_next_due(stream, first_due)


def _park_until_next_window(scheduler: CadenceScheduler, now: datetime) -> None:
    next_start = next_quote_start(now)
    for stream in STREAMS:
        scheduler.set_next_due(stream, next_start)


def run(root: Path, *, chunk: int, max_minutes: int, collector_commit: str) -> int:
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    runtime_path = root / "smoke_runtime.json"
    restart_path = root / "restart.json"
    runtime = SmokeRuntimeState.load_or_create(runtime_path, now)
    scheduler = CadenceScheduler(RestartState.load(restart_path))
    _initialize_due_times(scheduler, now)

    deadline = datetime.fromisoformat(runtime.deadline_utc).astimezone(UTC)
    chunk_end = min(deadline, now + timedelta(minutes=max_minutes))
    store = AppendOnlyStore(
        root,
        segment_name=f"observations-chunk-{chunk}.jsonl.gz",
        collector_commit=collector_commit,
    )
    client = ReadOnlyKalshiClient(timeout=10.0)
    store.append(
        source="smoke_control",
        payload={
            "event": "chunk_start",
            "chunk": chunk,
            "smoke_id": runtime.smoke_id,
            "scope": "24h_non_performance_integrity_smoke_only",
        },
        received_at=now,
        update_manifest=False,
    )

    last_manifest_sync = now
    last_state_save = now
    fatal_error: str | None = None

    try:
        while True:
            now = datetime.now(UTC)
            if now >= chunk_end or now >= deadline:
                break
            if not in_quote_window(now):
                _park_until_next_window(scheduler, now)
                runtime.save(runtime_path)
                scheduler.state.save(restart_path)
                sleep_for = min(5.0, max(0.1, (chunk_end - now).total_seconds()))
                time.sleep(sleep_for)
                continue

            due_metadata = _latest_due(scheduler, store, "metadata", now)
            if due_metadata is not None:
                try:
                    _collect_metadata(client, store, runtime, due_metadata)
                except Exception as exc:
                    _append_error(
                        store,
                        source="metadata_error",
                        endpoint="/markets",
                        params={"series_ticker": INITIAL_SERIES_TICKER},
                        scheduled_at=due_metadata,
                        requested_at=now,
                        exc=exc,
                    )
                scheduler.mark_received("metadata", scheduled_at=due_metadata, received_at=now)

            due_status = _latest_due(scheduler, store, "exchange_status", now)
            if due_status is not None:
                try:
                    _collect_exchange_status(client, store, due_status)
                except Exception as exc:
                    _append_error(
                        store,
                        source="exchange_status",
                        endpoint="/exchange/status",
                        params={},
                        scheduled_at=due_status,
                        requested_at=now,
                        exc=exc,
                    )
                scheduler.mark_received(
                    "exchange_status",
                    scheduled_at=due_status,
                    received_at=now,
                )

            due_incentives = _latest_due(scheduler, store, "incentives", now)
            if due_incentives is not None:
                try:
                    _collect_incentives(client, store, due_incentives)
                except Exception as exc:
                    _append_error(
                        store,
                        source="incentives",
                        endpoint="/incentive_programs",
                        params={"status": "active"},
                        scheduled_at=due_incentives,
                        requested_at=now,
                        exc=exc,
                    )
                scheduler.mark_received(
                    "incentives",
                    scheduled_at=due_incentives,
                    received_at=now,
                )

            due_books = _latest_due(scheduler, store, "book", now)
            if due_books is not None:
                try:
                    _collect_books(client, store, runtime, due_books)
                except Exception as exc:
                    _append_error(
                        store,
                        source="orderbooks_batch",
                        endpoint="/markets/orderbooks",
                        params={"tickers": runtime.active_markets},
                        scheduled_at=due_books,
                        requested_at=now,
                        exc=exc,
                    )
                scheduler.mark_received("book", scheduled_at=due_books, received_at=now)

            due_trades = _latest_due(scheduler, store, "trades", now)
            if due_trades is not None:
                try:
                    _collect_trades(client, store, scheduler, due_trades)
                except TradeContinuityError:
                    raise
                except Exception as exc:
                    _append_error(
                        store,
                        source="trades_global",
                        endpoint="/markets/trades",
                        params={"ticker": None},
                        scheduled_at=due_trades,
                        requested_at=now,
                        exc=exc,
                    )
                scheduler.mark_received("trades", scheduled_at=due_trades, received_at=now)

            now = datetime.now(UTC)
            if (now - last_state_save).total_seconds() >= 5:
                runtime.save(runtime_path)
                scheduler.state.save(restart_path)
                last_state_save = now
            if (now - last_manifest_sync).total_seconds() >= 60:
                store.sync_manifest()
                last_manifest_sync = now
            time.sleep(0.05)
    except Exception as exc:
        fatal_error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        finished = datetime.now(UTC)
        store.append(
            source="smoke_control",
            payload={
                "event": "chunk_end",
                "chunk": chunk,
                "smoke_id": runtime.smoke_id,
                "fatal_error": fatal_error,
            },
            received_at=finished,
            update_manifest=False,
        )
        if chunk not in runtime.chunks_completed:
            runtime.chunks_completed.append(chunk)
        runtime.save(runtime_path)
        scheduler.state.save(restart_path)
        store.sync_manifest()
        summary = {
            "smoke_id": runtime.smoke_id,
            "chunk": chunk,
            "chunk_finished_at_utc": finished.isoformat(),
            "deadline_utc": runtime.deadline_utc,
            "fatal_error": fatal_error,
            "active_market_count": len(runtime.active_markets),
            "event_count": len(runtime.event_tickers),
            "performance_blinded": True,
        }
        (root / f"chunk-summary-{chunk}.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n"
        )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--chunk", type=int, required=True)
    parser.add_argument("--max-minutes", type=int, default=330)
    args = parser.parse_args()
    commit = os.environ.get("GITHUB_SHA", "unknown")
    raise SystemExit(
        run(
            args.root,
            chunk=args.chunk,
            max_minutes=args.max_minutes,
            collector_commit=commit,
        )
    )


if __name__ == "__main__":
    main()
