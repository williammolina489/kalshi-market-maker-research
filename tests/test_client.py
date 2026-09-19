from kalshi_mm.client import ReadOnlyKalshiClient


def test_client_builds_public_get_urls_only() -> None:
    seen: list[str] = []

    def fake_transport(url: str, timeout: float) -> dict[str, object]:
        seen.append(url)
        assert timeout == 3.0
        return {"ok": True}

    client = ReadOnlyKalshiClient(timeout=3.0, transport=fake_transport)
    assert client.get_markets(series_ticker="KXHIGHNY", status="open", limit=25) == {
        "ok": True
    }
    assert seen == [
        "https://external-api.kalshi.com/trade-api/v2/markets?"
        "series_ticker=KXHIGHNY&status=open&limit=25"
    ]


def test_trade_query_excludes_block_trades() -> None:
    seen: list[str] = []

    def fake_transport(url: str, timeout: float) -> dict[str, object]:
        seen.append(url)
        return {}

    client = ReadOnlyKalshiClient(transport=fake_transport)
    client.get_trades(ticker="ABC", limit=100)
    assert "is_block_trade=false" in seen[0]
    assert "ticker=ABC" in seen[0]


def test_invalid_orderbook_depth_is_rejected_before_network() -> None:
    client = ReadOnlyKalshiClient(transport=lambda *_: {})
    try:
        client.get_orderbook("ABC", depth=101)
    except ValueError as exc:
        assert "depth" in str(exc)
    else:
        raise AssertionError("expected ValueError")
