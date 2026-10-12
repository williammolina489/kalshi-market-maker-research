from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest

from kalshi_mm.client import ReadOnlyKalshiClient
from kalshi_mm.collector import TradeContinuity, TradeContinuityError
from kalshi_mm.scheduler import CadenceScheduler, RestartState
from kalshi_mm.smoke_review import review
from kalshi_mm.smoke_runner import (
    SmokeRuntimeState,
    _collect_trades,
    _submit_fast_polls,
    next_quote_start,
)
from kalshi_mm.storage import AppendOnlyStore


def test_batch_orderbooks_use_repeated_ticker_query_params() -> None:
    seen: list[str] = []

    def transport(url: str, _: float) -> dict[str, object]:
        seen.append(url)
        return {"orderbooks": []}

    client = ReadOnlyKalshiClient(transport=transport)
    client.get_orderbooks(["A", "B"])
    assert "tickers=A&tickers=B" in seen[0]


def test_trade_query_can_be_exchange_wide_without_ticker() -> None:
    seen: list[str] = []

    def transport(url: str, _: float) -> dict[str, object]:
        seen.append(url)
        return {"trades": [], "cursor": ""}

    client = ReadOnlyKalshiClient(transport=transport)
    client.get_trades(ticker=None, limit=1000, min_ts=123)
    assert "ticker=" not in seen[0]
    assert "min_ts=123" in seen[0]
    assert "is_block_trade=false" in seen[0]


def test_restart_state_persists_trade_dedup_state(tmp_path: Path) -> None:
    state = RestartState(
        trade_cursor="cursor",
        trade_watermark="2026-10-01T13:00:00+00:00",
        seen_trade_ids={"__global__": ["a", "b"]},
        trade_cursors={"T": "market-cursor"},
        trade_watermarks={"T": "2026-10-01T13:00:00+00:00"},
    )
    path = tmp_path / "restart.json"
    state.save(path)
    assert RestartState.load(path) == state


def test_manifest_preserves_multiple_chunk_segments(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 13, 0, tzinfo=UTC)
    first = AppendOnlyStore(tmp_path, segment_name="observations-chunk-1.jsonl.gz")
    first.append(source="a", payload={"n": 1}, received_at=now)
    second = AppendOnlyStore(tmp_path, segment_name="observations-chunk-2.jsonl.gz")
    second.append(source="b", payload={"n": 2}, received_at=now + timedelta(seconds=1))

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert [entry["path"] for entry in manifest["segments"]] == [
        "observations-chunk-1.jsonl.gz",
        "observations-chunk-2.jsonl.gz",
    ]
    assert [row["payload"]["n"] for row in second.replay()] == [1, 2]


def test_smoke_runtime_deadline_is_exactly_24_hours(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 23, 40, tzinfo=UTC)
    state = SmokeRuntimeState.load_or_create(tmp_path / "runtime.json", now)
    started = datetime.fromisoformat(state.started_at_utc)
    deadline = datetime.fromisoformat(state.deadline_utc)
    assert deadline - started == timedelta(hours=24)


def test_next_quote_start_respects_new_york_time() -> None:
    before_open = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    after_close = datetime(2026, 10, 2, 20, 0, tzinfo=UTC)
    assert next_quote_start(before_open) == datetime(2026, 10, 2, 13, 0, tzinfo=UTC)
    assert next_quote_start(after_close) == datetime(2026, 10, 3, 13, 0, tzinfo=UTC)


def test_smoke_review_remains_performance_blinded(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    runtime = {
        "smoke_id": "test",
        "started_at_utc": (now - timedelta(hours=25)).isoformat(),
        "deadline_utc": (now - timedelta(hours=1)).isoformat(),
        "active_markets": [],
        "event_tickers": [],
        "chunks_completed": [1],
    }
    (tmp_path / "smoke_runtime.json").write_text(json.dumps(runtime))
    store = AppendOnlyStore(tmp_path, segment_name="observations-chunk-1.jsonl.gz")
    store.append(source="smoke_control", payload={"event": "test"}, received_at=now)
    summary = review(tmp_path)
    rendered = json.dumps(summary).lower()
    assert summary["performance_blinded"] is True
    assert summary["integrity_review_status"] == "REVIEW_REQUIRED"
    assert "pnl" not in rendered
    assert "sharpe" not in rendered
    assert "drawdown" not in rendered


def test_parallel_fast_polls_overlap_and_append_replayable_records(tmp_path: Path) -> None:
    both_started = Barrier(2, timeout=3)

    class PublicReadOnlyClient:
        def get_orderbooks(self, tickers):
            assert tickers == ["KXHIGHNY-A"]
            both_started.wait()
            return {"orderbooks": [{"ticker": "KXHIGHNY-A"}]}

        def get_trades(self, **kwargs):
            assert kwargs["ticker"] is None
            both_started.wait()
            return {"trades": [], "cursor": None}

    now = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)
    runtime = SmokeRuntimeState(
        smoke_id="local-replay-test",
        started_at_utc=now.isoformat(),
        deadline_utc=(now + timedelta(hours=1)).isoformat(),
        active_markets=["KXHIGHNY-A"],
    )
    scheduler = CadenceScheduler()
    for stream in ("book", "trades"):
        scheduler.set_next_due(stream, now)
    store = AppendOnlyStore(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        book_at, trades_at, book, trades = _submit_fast_polls(
            executor, PublicReadOnlyClient(), store, runtime, scheduler, now
        )
        assert book_at == trades_at == now
        assert book is not None and trades is not None
        book.result(timeout=3)
        trades.result(timeout=3)
    scheduler.mark_received("book", scheduled_at=book_at, received_at=now)
    scheduler.mark_received("trades", scheduled_at=trades_at, received_at=now)
    store.sync_manifest()
    replay = list(store.replay())
    assert sorted(row["source"] for row in replay) == [
        "orderbooks_batch",
        "trades_global",
    ]
    assert scheduler.state.next_due["book"] == (now + timedelta(seconds=1)).isoformat()
    assert scheduler.state.next_due["trades"] == (now + timedelta(seconds=1)).isoformat()


def test_concurrent_append_does_not_corrupt_gzip_manifest(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)

    def write_worker(source: str) -> None:
        for i in range(30):
            store.append(
                source=source,
                payload={"i": i},
                received_at=datetime(2026, 10, 1, 14, 0, tzinfo=UTC)
                + timedelta(seconds=i),
                update_manifest=False,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(write_worker, source) for source in ("book", "trades")]
        for job in jobs:
            job.result(timeout=8)
    store.sync_manifest()
    replay = list(store.replay())
    assert len(replay) == 60
    assert {row["source"] for row in replay} == {"book", "trades"}
    assert all(len(row["content_sha256"]) == 64 for row in replay)


def test_review_counts_actual_missing_slots_not_only_gap_records(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    start = now - timedelta(hours=25)
    (tmp_path / "smoke_runtime.json").write_text(
        json.dumps({
            "smoke_id": "gap-attribution-test",
            "started_at_utc": start.isoformat(),
            "deadline_utc": (now - timedelta(hours=1)).isoformat(),
        })
    )
    store = AppendOnlyStore(tmp_path)
    store.append(
        source="cadence_gap",
        payload={
            "stream": "book",
            "missing_count": 4,
            "first_missing_utc": start.isoformat(),
            "last_missing_utc": (start + timedelta(seconds=3)).isoformat(),
        },
        scheduled_at=start,
        received_at=start + timedelta(seconds=4),
        error="missed_scheduled_slots",
        update_manifest=False,
    )
    store.append(
        source="orderbooks_batch",
        payload={"orderbooks": [{"ticker": "A"}]},
        scheduled_at=start + timedelta(seconds=4),
        received_at=start + timedelta(seconds=5),
        update_manifest=False,
    )
    # Multiple trade pages at the same scheduled time are only one poll slot.
    for i in range(2):
        store.append(
            source="trades_global",
            payload={"trades": [{"trade_id": str(i)}]},
            scheduled_at=start + timedelta(seconds=4),
            received_at=start + timedelta(seconds=5 + i),
            update_manifest=False,
        )
    store.sync_manifest()
    summary = review(tmp_path)
    assert summary["cadence_gap_records"] == 1
    assert summary["missing_scheduled_slots_by_stream"] == {"book": 4}
    assert summary["attempted_scheduled_slots_by_stream"]["trades"] == 1
    assert summary["successful_scheduled_slots_by_stream"]["book"] == 1
    assert summary["performance_blinded"] is True


def test_review_rejects_malformed_gap_attribution(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    (tmp_path / "smoke_runtime.json").write_text(
        json.dumps({
            "smoke_id": "bad-gap-test",
            "started_at_utc": (now - timedelta(hours=25)).isoformat(),
            "deadline_utc": (now - timedelta(hours=1)).isoformat(),
        })
    )
    store = AppendOnlyStore(tmp_path)
    store.append(
        source="cadence_gap",
        payload={"stream": "book", "missing_count": -1},
        received_at=now,
    )
    import pytest
    with pytest.raises(ValueError, match="invalid cadence-gap"):
        review(tmp_path)


def test_scoped_continuity_ignores_unrelated_ids_but_preserves_pagination() -> None:
    continuity = TradeContinuity(ticker_prefix="KXHIGHNY-")
    page1 = {
        "trades": [
            {"ticker": "KXBTC-OTHER", "trade_id": f"other-{i}"}
            for i in range(3000)
        ] + [{"ticker": "KXHIGHNY-T", "trade_id": "target-1"}],
        "cursor": "next",
    }
    accepted = continuity.accept_page(page1, requested_cursor=None)
    assert [item["trade_id"] for item in accepted] == ["target-1"]
    assert continuity.seen_trade_ids == {"target-1"}
    assert continuity.cursor == "next"
    with pytest.raises(TradeContinuityError, match="cursor lineage"):
        continuity.accept_page(page1, requested_cursor="wrong")

    duplicate = {
        "trades": [
            {"ticker": "KXHIGHNY-T", "trade_id": "target-1"},
            {"ticker": "KXHIGHNY-T", "trade_id": "target-2"},
        ],
        "cursor": None,
    }
    accepted = continuity.accept_page(duplicate, requested_cursor="next")
    assert [item["trade_id"] for item in accepted] == ["target-2"]
    assert continuity.seen_trade_ids == {"target-1", "target-2"}


def test_scoped_continuity_fails_closed_on_trade_without_ticker() -> None:
    continuity = TradeContinuity(ticker_prefix="KXHIGHNY-")
    with pytest.raises(TradeContinuityError, match="ticker"):
        continuity.accept_page(
            {"trades": [{"trade_id": "cannot-identify"}], "cursor": None},
            requested_cursor=None,
        )


def test_global_watermark_advances_without_relevant_trades(tmp_path: Path) -> None:
    class MockGlobalClient:
        def __init__(self) -> None:
            self.requests = []

        def get_trades(self, *, ticker, limit, cursor, min_ts):
            self.requests.append({"ticker": ticker, "cursor": cursor, "min_ts": min_ts})
            return {
                "trades": [
                    {
                        "ticker": "KXBTC-OTHER",
                        "trade_id": "other",
                        "created_time": "2026-10-01T14:00:03Z",
                    }
                ],
                "cursor": None,
            }

    now = datetime(2026, 10, 1, 14, 0, 5, tzinfo=UTC)
    scheduler = CadenceScheduler()
    store = AppendOnlyStore(tmp_path)
    client = MockGlobalClient()
    _collect_trades(client, store, scheduler, now)
    assert scheduler.state.trade_watermark == "2026-10-01T14:00:03+00:00"
    assert scheduler.state.seen_trade_ids["__global__"] == []
    _collect_trades(client, store, scheduler, now + timedelta(seconds=1))
    assert client.requests[1]["min_ts"] == int(
        datetime(2026, 10, 1, 14, 0, 3, tzinfo=UTC).timestamp()
    ) - 1
    assert scheduler.state.seen_trade_ids["__global__"] == []
    store.sync_manifest()
    assert len(list(store.replay())) == 2
