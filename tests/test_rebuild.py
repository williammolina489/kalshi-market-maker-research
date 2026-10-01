from __future__ import annotations

import gzip
import hashlib
import inspect
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from kalshi_mm.client import ReadOnlyKalshiClient
from kalshi_mm.collector import Collector, TradeContinuity, TradeContinuityError
from kalshi_mm.economics import (
    derive_top_of_book,
    eligible_for_quote,
    in_quote_window,
    is_on_tick,
    parse_book,
    resolve_tick,
    spread_ticks,
)
from kalshi_mm.models import BookLevel, IntegrityError, PriceRange, RawTrade
from kalshi_mm.scheduler import CadenceScheduler, RestartState
from kalshi_mm.simulation import Inventory, initialize_quote
from kalshi_mm.smoke import SmokeReport
from kalshi_mm.storage import AppendOnlyStore

ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 9, 22, 12, 0, tzinfo=ET)
UTC_NOW = NOW.astimezone(UTC)
RANGES = (
    PriceRange(Decimal("0.00"), Decimal("0.49"), Decimal("0.01")),
    PriceRange(Decimal("0.50"), Decimal("1.00"), Decimal("0.05")),
)


def top(
    bid: str = "0.40",
    no_bid: str = "0.55",
    bid_size: str = "12",
    ask_size: str = "12",
):
    return derive_top_of_book(
        "T",
        (BookLevel(Decimal(bid), Decimal(bid_size)),),
        (BookLevel(Decimal(no_bid), Decimal(ask_size)),),
    )


def trade(
    *,
    trade_id: str = "x",
    price: str = "0.40",
    count: str = "1",
    side: str = "ask",
    block: bool = False,
    ticker: str = "T",
) -> RawTrade:
    return RawTrade(
        trade_id=trade_id,
        market_ticker=ticker,
        created_at_utc=UTC_NOW,
        count=Decimal(count),
        yes_price=Decimal(price),
        taker_book_side=side,
        is_block_trade=block,
    )


def eligible(**overrides) -> bool:
    params = {
        "status": "active",
        "timestamp": NOW,
        "close_time": NOW + timedelta(hours=2),
        "top": top(),
        "price_ranges": RANGES,
        "fees_resolved": True,
        "rules_resolved": True,
    }
    params.update(overrides)
    return eligible_for_quote(**params)


def test_discovery_query_is_frozen_series() -> None:
    seen = []

    def transport(url: str, _: float):
        seen.append(url)
        return {"markets": []}

    client = ReadOnlyKalshiClient(transport=transport)
    client.get_markets(series_ticker="KXHIGHNY", status="open", limit=100)
    assert "series_ticker=KXHIGHNY" in seen[0]
    assert "status=open" in seen[0]


def test_collector_discovers_child_markets(tmp_path: Path) -> None:
    class FakeClient:
        def get_markets(self, **kwargs):
            assert kwargs["series_ticker"] == "KXHIGHNY"
            return {
                "markets": [
                    {"ticker": "KXHIGHNY-A", "series_ticker": "KXHIGHNY"},
                    {"ticker": "KXHIGHNY-B", "series_ticker": "KXHIGHNY"},
                ]
            }

    collector = Collector(FakeClient(), AppendOnlyStore(tmp_path))
    assert collector.discover_markets(now=UTC_NOW) == ["KXHIGHNY-A", "KXHIGHNY-B"]


def test_parse_book_preserves_complete_yes_no_depth() -> None:
    payload = {
        "orderbook_fp": {
            "yes_dollars": [["0.40", "12"], ["0.39", "20"]],
            "no_dollars": [["0.55", "11"], ["0.56", "30"]],
        }
    }
    book = parse_book(payload, observed_at_utc=UTC_NOW, market_ticker="T")
    assert [level.price for level in book.yes_bids] == [Decimal("0.40"), Decimal("0.39")]
    assert [level.price for level in book.no_bids] == [Decimal("0.55"), Decimal("0.56")]


def test_fixed_point_fractional_quantities_are_lossless() -> None:
    book = parse_book(
        {
            "orderbook_fp": {
                "yes_dollars": [["0.40", "12.5"]],
                "no_dollars": [["0.55", "11.25"]],
            }
        },
        observed_at_utc=UTC_NOW,
        market_ticker="T",
    )
    assert book.yes_bids[0].count == Decimal("12.5")
    assert book.no_bids[0].count == Decimal("11.25")


def test_multiple_price_ranges_resolve_local_ticks() -> None:
    assert resolve_tick(Decimal("0.40"), RANGES) == Decimal("0.01")
    assert resolve_tick(Decimal("0.60"), RANGES) == Decimal("0.05")


def test_off_tick_prices_are_rejected() -> None:
    assert not is_on_tick(Decimal("0.61"), RANGES)
    assert is_on_tick(Decimal("0.60"), RANGES)


def test_quote_window_uses_america_new_york_and_dst() -> None:
    summer = datetime(2026, 7, 1, 13, 0, tzinfo=UTC)
    winter = datetime(2026, 12, 1, 14, 0, tzinfo=UTC)
    assert in_quote_window(summer)
    assert in_quote_window(winter)


def test_quote_window_rejects_before_open_and_after_close() -> None:
    assert not in_quote_window(datetime(2026, 9, 22, 8, 59, 59, tzinfo=ET))
    assert not in_quote_window(datetime(2026, 9, 22, 15, 30, 1, tzinfo=ET))


def test_close_requirement_is_at_least_sixty_minutes() -> None:
    assert eligible(close_time=NOW + timedelta(minutes=60))
    assert not eligible(close_time=NOW + timedelta(minutes=59, seconds=59))


def test_two_sided_book_is_required() -> None:
    with pytest.raises(ValueError, match="two-sided"):
        derive_top_of_book("T", (BookLevel(Decimal("0.40"), Decimal("12")),), ())


def test_top_level_size_gate_is_ten_contracts_each_side() -> None:
    assert eligible(top=top(bid_size="10", ask_size="10"))
    assert not eligible(top=top(bid_size="9.99", ask_size="10"))


def test_spread_gate_requires_three_local_ticks() -> None:
    assert spread_ticks(top(bid="0.40", no_bid="0.57"), RANGES) == 3
    assert not eligible(top=top(bid="0.40", no_bid="0.58"))


def test_equal_size_microprice_uses_frozen_formula() -> None:
    assert top().microprice == Decimal("0.425")


def test_quote_joins_best_price_without_improving() -> None:
    current = top()
    bid = initialize_quote(
        ticker="T",
        side="bid",
        price=current.best_yes_bid,
        displayed_size=current.best_bid_size,
        now=UTC_NOW,
    )
    ask = initialize_quote(
        ticker="T",
        side="ask",
        price=current.best_yes_ask,
        displayed_size=current.best_ask_size,
        now=UTC_NOW,
    )
    assert bid.price == current.best_yes_bid
    assert ask.price == current.best_yes_ask


def test_minimum_rest_blocks_non_safety_reprice_before_30_seconds() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=5, now=UTC_NOW
    )
    assert not q.should_reprice(
        UTC_NOW + timedelta(seconds=29),
        price=Decimal("0.41"),
        fair_value=Decimal("0.43"),
        prior_fair_value=Decimal("0.42"),
        tick=Decimal("0.01"),
        spread_ticks=5,
        eligible=True,
    )


def test_maximum_rest_forces_reprice_at_300_seconds() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=5, now=UTC_NOW
    )
    assert q.should_reprice(
        UTC_NOW + timedelta(seconds=300),
        price=q.price,
        fair_value=Decimal("0.42"),
        prior_fair_value=Decimal("0.42"),
        tick=Decimal("0.01"),
        spread_ticks=5,
        eligible=True,
    )


def test_reprice_creates_fresh_queue_position() -> None:
    old = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=12, now=UTC_NOW
    )
    old.consume_trade(trade(count="5"))
    new = initialize_quote(
        ticker="T",
        side="bid",
        price=Decimal("0.41"),
        displayed_size=Decimal("3"),
        now=UTC_NOW + timedelta(seconds=30),
    )
    assert old.queue_ahead == Decimal("7")
    assert new.queue_ahead == Decimal("3")


def test_hard_safety_ineligibility_cancels_immediately() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=5, now=UTC_NOW
    )
    assert q.should_reprice(
        UTC_NOW + timedelta(seconds=1),
        price=q.price,
        fair_value=Decimal("0.42"),
        prior_fair_value=Decimal("0.42"),
        tick=Decimal("0.01"),
        spread_ticks=5,
        eligible=False,
    )


def test_queue_initializes_behind_entire_displayed_size() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=12, now=UTC_NOW
    )
    assert q.queue_ahead == Decimal("12")


def test_depth_disappearance_gives_zero_queue_credit() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=12, now=UTC_NOW
    )
    q.observe_depth(Decimal("1"), observed_at=UTC_NOW + timedelta(seconds=1))
    assert q.queue_ahead == Decimal("12")


def test_qualifying_exact_price_trade_consumes_queue_then_fills() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=5, now=UTC_NOW
    )
    assert q.consume_trade(trade(count="12")) == Decimal("7")
    assert q.queue_ahead == 0


def test_wrong_price_trade_never_fills() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=0, now=UTC_NOW
    )
    assert q.consume_trade(trade(price="0.39", count="10")) == 0


def test_wrong_side_trade_never_fills() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=0, now=UTC_NOW
    )
    assert q.consume_trade(trade(side="bid", count="10")) == 0


def test_block_trade_never_fills() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=0, now=UTC_NOW
    )
    assert q.consume_trade(trade(block=True, count="10")) == 0


def test_partial_fill_is_excess_after_queue() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=5, now=UTC_NOW
    )
    assert q.consume_trade(trade(count="7")) == Decimal("2")
    assert q.remaining == Decimal("8.00")


def test_queue_accounting_is_cumulative_across_trades() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=12, now=UTC_NOW
    )
    assert q.consume_trade(trade(trade_id="a", count="12")) == 0
    assert q.consume_trade(trade(trade_id="b", count="7")) == Decimal("7")


def test_fill_is_capped_at_remaining_quote_size() -> None:
    q = initialize_quote(
        ticker="T", side="bid", price=Decimal("0.40"), displayed_size=0, now=UTC_NOW
    )
    assert q.consume_trade(trade(count="100")) == Decimal("10.00")
    assert q.remaining == 0


def test_per_market_inventory_limit() -> None:
    inv = Inventory()
    inv.apply("T", Decimal("20"))
    assert not inv.can_fill("T", Decimal("1"))
    with pytest.raises(ValueError, match="inventory limit"):
        inv.apply("T", Decimal("1"))


def test_aggregate_inventory_limit_boundary() -> None:
    inv = Inventory()
    inv.apply("T", Decimal("20"))
    inv.apply("U", Decimal("20"))
    assert inv.aggregate_absolute == Decimal("40")
    assert not inv.can_fill("V", Decimal("1"))


def test_aggregate_inventory_below_boundary_allows_fill() -> None:
    inv = Inventory()
    inv.apply("T", Decimal("10"))
    inv.apply("U", Decimal("20"))
    assert inv.can_fill("V", Decimal("1"))


def test_risk_reducing_side_remains_allowed_at_limit() -> None:
    inv = Inventory()
    inv.apply("T", Decimal("20"))
    inv.apply("U", Decimal("20"))
    assert inv.can_fill("T", Decimal("-1"))
    inv.apply("T", Decimal("-1"))
    assert inv.aggregate_absolute == Decimal("39")


def test_trade_dedup_is_by_trade_identity() -> None:
    continuity = TradeContinuity()
    page = {"trades": [{"trade_id": "a"}], "cursor": "c"}
    assert [row["trade_id"] for row in continuity.accept_page(page, requested_cursor=None)] == ["a"]
    continuity.cursor = None
    assert continuity.accept_page(page, requested_cursor=None) == []


def test_trade_cursor_gap_fails_closed() -> None:
    continuity = TradeContinuity(cursor="expected")
    with pytest.raises(TradeContinuityError, match="cursor lineage"):
        continuity.accept_page({"trades": [], "cursor": None}, requested_cursor="wrong")


def test_restart_state_round_trip(tmp_path: Path) -> None:
    state = RestartState(
        next_due={"book": UTC_NOW.isoformat()},
        trade_cursor="abc",
        trade_watermark="2026-09-22T16:00:00Z",
        last_received={"book": UTC_NOW.isoformat()},
    )
    path = tmp_path / "restart.json"
    state.save(path)
    assert RestartState.load(path) == state


def test_append_only_raw_writes_preserve_prior_records(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path, collector_commit="abc")
    store.append(source="book", payload={"x": 1}, received_at=UTC_NOW)
    store.append(source="book", payload={"x": 2}, received_at=UTC_NOW + timedelta(seconds=1))
    with gzip.open(store.segment, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    assert [row["payload"]["x"] for row in rows] == [1, 2]


def test_manifest_hash_matches_segment(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)
    store.append(source="book", payload={"x": 1}, received_at=UTC_NOW)
    manifest = json.loads(store.manifest.read_text())
    expected = hashlib.sha256(store.segment.read_bytes()).hexdigest()
    assert manifest["segments"][0]["sha256"] == expected


def test_replay_verifies_records_and_returns_payload(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)
    store.append(source="book", payload={"x": 1}, received_at=UTC_NOW)
    rows = list(store.replay())
    assert rows[0]["payload"] == {"x": 1}
    assert len(rows[0]["content_sha256"]) == 64


def test_corrupt_segment_fails_closed(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)
    store.append(source="book", payload={"x": 1}, received_at=UTC_NOW)
    with store.segment.open("ab") as handle:
        handle.write(b"bad")
    with pytest.raises(ValueError):
        list(store.replay())


def test_malformed_orderbook_fails_closed() -> None:
    with pytest.raises(ValueError, match="complete YES/NO"):
        parse_book(
            {"orderbook_fp": {"yes_dollars": [], "no_dollars": []}},
            observed_at_utc=UTC_NOW,
            market_ticker="T",
        )


def test_closed_or_stale_market_response_is_ineligible() -> None:
    assert not eligible(status="closed")
    assert not eligible(timestamp=datetime(2026, 9, 22, 8, 0, tzinfo=ET))


def test_missed_slots_are_explicit_not_synthesized() -> None:
    scheduler = CadenceScheduler()
    scheduler.set_next_due("book", UTC_NOW)
    slots = scheduler.due_slots("book", UTC_NOW + timedelta(seconds=3))
    assert slots == [
        UTC_NOW,
        UTC_NOW + timedelta(seconds=1),
        UTC_NOW + timedelta(seconds=2),
        UTC_NOW + timedelta(seconds=3),
    ]


def test_smoke_report_contains_no_performance_metrics() -> None:
    keys = {key.lower() for key in SmokeReport().as_dict()}
    forbidden = {
        "pnl",
        "gross_pnl",
        "net_pnl",
        "sharpe",
        "drawdown",
        "return",
        "economic_pass",
    }
    assert keys.isdisjoint(forbidden)
    rendered = json.dumps(SmokeReport().as_dict()).lower()
    assert "pnl" not in rendered and "sharpe" not in rendered and "drawdown" not in rendered


def test_client_has_no_order_or_mutating_http_surface() -> None:
    public_names = {
        name.lower() for name, _ in inspect.getmembers(ReadOnlyKalshiClient, inspect.isfunction)
    }
    forbidden = {"post", "put", "delete", "place_order", "cancel_order", "amend_order"}
    assert public_names.isdisjoint(forbidden)


def test_frozen_collection_cadence_is_preserved() -> None:
    assert CadenceScheduler.CADENCE_SECONDS == {
        "book": 1,
        "trades": 1,
        "metadata": 30,
        "exchange_status": 5,
        "incentives": 60,
    }


def test_fee_and_rule_metadata_are_required() -> None:
    assert not eligible(fees_resolved=False)
    assert not eligible(rules_resolved=False)


def test_pause_and_integrity_flags_fail_closed() -> None:
    assert not eligible(paused=True)
    assert not eligible(integrity_ok=False)


def test_microprice_must_be_one_tick_inside_each_side() -> None:
    unbalanced = top(bid="0.40", no_bid="0.55", bid_size="100", ask_size="1")
    assert not eligible(top=unbalanced)


def test_locked_or_crossed_books_fail_closed() -> None:
    with pytest.raises(ValueError, match="locked or crossed"):
        top(bid="0.50", no_bid="0.50")


def test_record_hash_changes_when_payload_changes(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)
    first = store.append(source="book", payload={"x": 1}, received_at=UTC_NOW)
    second = store.append(
        source="book", payload={"x": 2}, received_at=UTC_NOW + timedelta(seconds=1)
    )
    assert first != second


def test_non_monotonic_source_timestamp_fails_replay(tmp_path: Path) -> None:
    store = AppendOnlyStore(tmp_path)
    store.append(source="book", payload={"x": 1}, received_at=UTC_NOW + timedelta(seconds=1))
    store.append(source="book", payload={"x": 2}, received_at=UTC_NOW)
    with pytest.raises(IntegrityError, match="non-monotonic"):
        list(store.replay())


def test_incentive_cursor_is_supported_by_read_only_client() -> None:
    seen = []

    def transport(url: str, _: float):
        seen.append(url)
        return {}

    ReadOnlyKalshiClient(transport=transport).get_incentives(cursor="next")
    assert "cursor=next" in seen[0]


def test_scheduler_uses_scheduled_time_not_receive_time_for_next_due() -> None:
    scheduler = CadenceScheduler()
    scheduler.mark_received(
        "book",
        scheduled_at=UTC_NOW,
        received_at=UTC_NOW + timedelta(milliseconds=750),
    )
    assert scheduler.state.next_due["book"] == (UTC_NOW + timedelta(seconds=1)).isoformat()


def test_naive_timestamps_fail_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        in_quote_window(datetime(2026, 9, 22, 12, 0))
