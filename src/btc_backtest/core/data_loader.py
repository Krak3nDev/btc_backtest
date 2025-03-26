import asyncio
import os
from datetime import datetime

import httpx
import pandas as pd

from btc_backtest.core.binance.cache_manager import CacheManager, load_checksums
from btc_backtest.core.binance.fetcher import BinanceFetcher
from btc_backtest.core.binance.parser import parse_kline_zip


class BinanceDataLoader:
    """
    Orchestrator: combines the functionality of Fetcher, CacheManager, and Parser.
    It provides methods:
     - download_monthly_klines(...) : downloads a CSV file for a specific month/year
     - load_data_for_period(...)    : downloads data for a range (start_year..end_year)
     - load_all_symbols(...)        : handles a list of symbols
    """

    def __init__(
        self,
        fetcher: BinanceFetcher,
        cache: CacheManager,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
        interval: str = "1m",
    ):
        self.fetcher = fetcher
        self.cache = cache
        self._start_year = start_year
        self._start_month = start_month
        self._end_year = end_year
        self._end_month = end_month
        self._interval = interval

    async def download_monthly_klines(
        self, symbol: str, year: int, month: int
    ) -> pd.DataFrame:
        """
        1) Checks the cache (CacheManager) to see if the file already exists.
        2) If it doesn't exist or is corrupted, downloads it from BinanceFetcher.
        3) If a 404 status is received, returns an empty DataFrame.
        4) Unpacks (BinanceDataParser) and returns the resulting DataFrame.
        """
        # 1) Attempt to retrieve from the cache
        cached_bytes = self.cache.get_cached_file(symbol, self._interval, year, month)
        if cached_bytes is not None:
            print(
                f"[CACHE HIT] Using the local file for {symbol}, {year}-{month:02d}"
            )
            # Unpack and parse
            return parse_kline_zip(cached_bytes)
        else:
            # 2) If the file is missing or invalid, download it
            try:
                content = await self.fetcher.fetch_kline_zip(
                    symbol, self._interval, year, month
                )
            except httpx.HTTPError as e:
                print(
                    f"Error downloading (with retries) {symbol} {year}-{month:02d}: {e}"
                )
                return pd.DataFrame()

            if content == b"404_NOT_FOUND":
                print(
                    f"Failed to download (404) {symbol}-{self._interval}-{year}-{month:02d}.zip"
                )
                return pd.DataFrame()

            # 3) Save the file to the cache
            self.cache.save_file(symbol, self._interval, year, month, content)
            # 4) Parse the file
            return parse_kline_zip(content)

    async def load_data_for_period(self, symbol: str) -> pd.DataFrame:
        """
        Downloads and concatenates monthly data for the specified symbol
        for the period from [start_year, start_month] to [end_year, end_month].
        """
        start_date = datetime(self._start_year, self._start_month, 1)
        end_date = datetime(self._end_year, self._end_month, 1)

        tasks = []
        current_date = start_date

        # Using an asyncio TaskGroup (Python 3.11+)
        async with asyncio.TaskGroup() as tg:
            while current_date <= end_date:
                y = current_date.year
                m = current_date.month
                task = tg.create_task(self.download_monthly_klines(symbol, y, m))
                tasks.append(task)

                if m == 12:
                    current_date = datetime(y + 1, 1, 1)
                else:
                    current_date = datetime(y, m + 1, 1)

        dataframes = [t.result() for t in tasks if not t.result().empty]

        if not dataframes:
            print(f"No data collected for symbol {symbol}.")
            return pd.DataFrame()

        full_data = pd.concat(dataframes, ignore_index=True)
        return full_data

    async def load_all_symbols(self, symbols: list[str]) -> dict[str, pd.DataFrame]:
        """
        Downloads data for a list of symbols.
        Returns a dictionary of the form { 'SYMBOL': DataFrame }.
        """
        async with asyncio.TaskGroup() as tg:
            tasks = {s: tg.create_task(self.load_data_for_period(s)) for s in symbols}
        results = {}
        for s, t in tasks.items():
            results[s] = t.result()
        return results


def save_aggregated_parquet(results: dict[str, pd.DataFrame], outfile: str) -> None:
    """
    Merges all DataFrames from the `results` dictionary into a single DataFrame
    and saves it in Parquet format using Snappy compression.

    :param results: A dict where the key is a symbol and the value is a pd.DataFrame.
    :param outfile: Path to the output .parquet file (relative or absolute).
    """
    # Convert to an absolute path based on the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    outfile_path = os.path.join(current_dir, outfile)

    # Keep only non-empty DataFrames
    results = {sym: df for sym, df in results.items() if not df.empty}
    if not results:
        print("All DataFrames are empty – nothing to save.")
        return

    # Merge all DataFrames
    all_data = pd.concat(results.values(), ignore_index=True)

    if all_data.empty:
        print("No data to save.")
        return

    # Save to Parquet with Snappy compression
    all_data.to_parquet(outfile_path, compression="snappy", index=False)
    print(f"Data saved to {outfile_path} (Snappy compression).")


async def main() -> None:
    top_100_btc = [
        "WBTCBTC",
        "ETHBTC",
        "SOLBTC",
        "BNBBTC",
        "DOGEBTC",
        "XRPBTC",
        "REDBTC",
    ]

    async with httpx.AsyncClient() as client:
        fetcher = BinanceFetcher(client=client)

        checksums_file = "checksums.txt"
        checksums = load_checksums(checksums_file)

        cache = CacheManager(
            cache_dir="cache", checksums=checksums, checksums_file=checksums_file
        )

        loader = BinanceDataLoader(
            fetcher=fetcher,
            cache=cache,
            start_year=2025,
            start_month=2,
            end_year=2025,
            end_month=2,
            interval="1m",
        )

        results = await loader.load_all_symbols(top_100_btc)

        save_aggregated_parquet(results, "data/binance_1m_data.parquet")


if __name__ == "__main__":
    asyncio.run(main())
