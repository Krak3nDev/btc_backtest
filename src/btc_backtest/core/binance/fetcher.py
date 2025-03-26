from httpx import AsyncClient, RequestError, HTTPStatusError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class BinanceFetcher:
    """
    A simple class to fetch klines data from Binance in ZIP format.
    Utilizes an AsyncClient for HTTP requests and Tenacity for retries.
    """

    def __init__(self, client: AsyncClient) -> None:
        """
        Initializes the BinanceFetcher with an asynchronous HTTP client.

        :param client: An httpx.AsyncClient instance for making HTTP requests.
        """
        self._client = client
        self._base_url = "https://data.binance.vision"

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RequestError, HTTPStatusError)),
    )
    async def _fetch_url_with_retry(self, url: str) -> bytes:
        """
        Fetches the content of a given URL, retrying on RequestError or HTTPStatusError.
        Tenacity is used to manage the retry mechanism.

        :param url: The URL to fetch.
        :return: The raw bytes of the requested resource, or b"404_NOT_FOUND" if the server returns a 404 status.
        :raises HTTPStatusError: If the response status is an error (4xx/5xx) other than 404.
        """
        response = await self._client.get(url, timeout=30.0)
        if response.status_code == 404:
            return b"404_NOT_FOUND"
        response.raise_for_status()
        return response.content

    async def fetch_kline_zip(
        self, symbol: str, interval: str, year: int, month: int
    ) -> bytes:
        """
        Builds the URL for a kline ZIP file, then calls _fetch_url_with_retry to obtain it.

        :param symbol: Trading symbol (e.g., 'BTCUSDT').
        :param interval: Kline interval (e.g., '1h', '1d').
        :param year: Year of the data.
        :param month: Month of the data.
        :return: The raw bytes of the ZIP file, or b"404_NOT_FOUND" if the server returns a 404 status.
        """
        base_url = f"{self._base_url}/data/spot/monthly/klines"
        filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
        url = f"{base_url}/{symbol}/{interval}/{filename}"

        content = await self._fetch_url_with_retry(url)
        return content
