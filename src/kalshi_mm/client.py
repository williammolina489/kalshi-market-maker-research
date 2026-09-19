"""Small, intentionally read-only client for Kalshi public market-data endpoints."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import PRODUCTION_BASE_URL, USER_AGENT

JsonDict = dict[str, Any]
Transport = Callable[[str, float], JsonDict]


def _stdlib_get_json(url: str, timeout: float) -> JsonDict:
    request = Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class ReadOnlyKalshiClient:
    """GET-only client.

    There is deliberately no generic request method, authentication support, or order endpoint.
    """

    def __init__(
        self,
        base_url: str = PRODUCTION_BASE_URL,
        *,
        timeout: float = 10.0,
        transport: Transport | None = None,
    ) -> None:
        normalized = base_url.rstrip("/")
        if not normalized.startswith("https://"):
            raise ValueError("Kalshi base URL must use HTTPS")
        self._base_url = normalized
        self._timeout = timeout
        self._transport = transport or _stdlib_get_json

    def _get(self, path: str, params: Mapping[str, object] | None = None) -> JsonDict:
        if not path.startswith("/") or ".." in path:
            raise ValueError("invalid API path")
        query = urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = f"{self._base_url}{path}"
        if query:
            url = f"{url}?{query}"
        return self._transport(url, self._timeout)

    def get_exchange_status(self) -> JsonDict:
        return self._get("/exchange/status")

    def get_series(self, ticker: str) -> JsonDict:
        return self._get(f"/series/{ticker}")

    def get_markets(
        self, *, series_ticker: str, status: str = "open", limit: int = 100
    ) -> JsonDict:
        return self._get(
            "/markets",
            {"series_ticker": series_ticker, "status": status, "limit": limit},
        )

    def get_market(self, ticker: str) -> JsonDict:
        return self._get(f"/markets/{ticker}")

    def get_orderbook(self, ticker: str, *, depth: int = 0) -> JsonDict:
        if depth < 0 or depth > 100:
            raise ValueError("depth must be between 0 and 100")
        return self._get(f"/markets/{ticker}/orderbook", {"depth": depth})

    def get_trades(
        self,
        *,
        ticker: str,
        limit: int = 1000,
        cursor: str | None = None,
        min_ts: int | None = None,
    ) -> JsonDict:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        return self._get(
            "/markets/trades",
            {
                "ticker": ticker,
                "limit": limit,
                "cursor": cursor,
                "min_ts": min_ts,
                "is_block_trade": "false",
            },
        )

    def get_incentives(self, *, status: str = "active", limit: int = 1000) -> JsonDict:
        return self._get(
            "/incentive_programs",
            {"status": status, "limit": limit},
        )
