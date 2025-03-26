import asyncio
from typing import NamedTuple, Any, TypeAlias

import httpx
from httpx import AsyncClient, RequestError, HTTPStatusError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class SymbolVolume(NamedTuple):
    symbol: str
    volume: float

TickerData: TypeAlias = list[dict[str, Any]]

class PairsFetcher:
    def __init__(
        self, client: AsyncClient, base_url: str = "https://api.binance.com/"
    ) -> None:
        """
        :param client: asynchronous HTTP client (httpx.AsyncClient)
        :param base_url: base URL for the Binance API
        """
        self._client = client
        self._base_url = base_url

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RequestError, HTTPStatusError)),
    )
    async def get_top_pairs(self, quote: str = "BTC", limit: int = 100) -> list[str]:
        """
        Asynchronously retrieves data from https://api.binance.com/api/v3/ticker/24hr,
        filters pairs that end with 'quote' (default "BTC"), sorts by 'quoteVolume'
        in descending order, discards pairs containing 'TEST', 'STUB', or 'EVENT',
        and returns the list of the top 'limit' symbols in a format like "ETH/BTC", "SOL/BTC", etc.
        """
        # 1) Load 24-hour statistics
        data = await self._fetch_24hr_ticker_data()

        # 2) Filter by quote, remove TEST/STUB/EVENT, keep (symbol, quoteVolume)
        filtered = self._filter_symbols(data, quote)

        # 3) Sort and take the top-N
        top_pairs = self._sort_and_select_top(filtered, limit)

        return [sym for (sym, vol) in top_pairs]

    async def _fetch_24hr_ticker_data(self) -> TickerData:
        """
        Sends a request to Binance and retrieves the list returned by the endpoint:
          GET /api/v3/ticker/24hr

        :return: a list of objects, each containing fields like 'symbol', 'quoteVolume', etc.
        """
        url = self._base_url + "api/v3/ticker/24hr"
        response = await self._client.get(url, timeout=15.0)
        # If status is 4xx or 5xx (except 404), a retry will be triggered (via tenacity).
        # 404 will also raise an exception if not handled before raise_for_status().
        response.raise_for_status()
        return response.json()

    def _filter_symbols(self, data: TickerData, quote: str) -> list[SymbolVolume]:
        """
        From all 'symbol' values, select those that end with 'quote' (e.g., 'BTC'),
        exclude symbols containing 'TEST', 'STUB', 'EVENT',
        and create (symbol, quoteVolume) tuples.
        """
        filtered = []
        for item in data:
            symbol = item["symbol"]

            # Check if it ends with 'quote'
            if not symbol.endswith(quote):
                continue

            # Exclude test-like pairs
            if any(x in symbol.upper() for x in ["TEST", "STUB", "EVENT"]):
                continue

            # Read the trading volume
            quote_volume = float(item.get("quoteVolume", 0.0))

            filtered.append(SymbolVolume(symbol, quote_volume))

        return filtered

    def _sort_and_select_top(
        self, filtered: list[SymbolVolume], limit: int
    ) -> list[SymbolVolume]:
        """
        Sorts the list (symbol, volume) by volume in descending order
        and returns the first 'limit' items.
        """
        filtered.sort(key=lambda x: x[1], reverse=True)
        return filtered[:limit]


async def main() -> None:
    async with httpx.AsyncClient() as http_client:
        fetcher = PairsFetcher(http_client)
        top_100_btc = await fetcher.get_top_pairs(quote="BTC", limit=100)
        print(top_100_btc)


if __name__ == "__main__":
    asyncio.run(main())
