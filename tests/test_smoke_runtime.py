from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from kalshi_mm.client import ReadOnlyKalshiClient
from kalshi_mm.scheduler import RestartState
from kalshi_mm.smoke_review import review
from kalshi_mm.smoke_runner import SmokeRuntimeState, next_quote_start
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
