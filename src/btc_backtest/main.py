import asyncio
import httpx
import pandas as pd
import os

# Local imports for your project
from btc_backtest.core.binance.binance_client import PairsFetcher
from btc_backtest.core.binance.cache_manager import load_checksums, CacheManager
from btc_backtest.core.binance.fetcher import BinanceFetcher
from btc_backtest.core.data_loader import BinanceDataLoader, save_aggregated_parquet

from btc_backtest.strategies.sma_cross import SmaCrossoverStrategy
from btc_backtest.strategies.rsi_bollinger import RsiBollingerStrategy
from btc_backtest.strategies.volume_spike_breakout import VolumeSpikeBreakoutStrategy

from core.backtester import Backtester


# Determine the absolute path to this file (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main_path(*subpaths: str) -> str:
    """
    A helper function to build an absolute path based on the directory
    where this main.py file is located. Useful for ensuring all data/results
    are read/written relative to the project structure.
    """
    return str(os.path.join(BASE_DIR, *subpaths))


async def main() -> None:
    """
    The main entry point for:
      - Fetching top-100 Binance BTC-quoted pairs
      - Downloading 1-minute OHLCV data for February 2025
      - Caching and saving data to parquet
      - Running multiple strategies via the Backtester
      - Generating metrics, equity curve charts, heatmaps, and optional HTML report
    """

    # Make sure pandas doesn't downcast certain numeric types silently
    pd.set_option("future.no_silent_downcasting", True)

    async with httpx.AsyncClient() as client:
        # 1) Retrieve the list of top-100 pairs quoted in BTC from Binance
        pairs_fetcher = PairsFetcher(client)
        top_100_btc = await pairs_fetcher.get_top_pairs(quote="BTC", limit=100)

        # 2) Set up the BinanceFetcher
        fetcher = BinanceFetcher(client=client)

        # 3) Prepare cache-related functionality
        checksums_file = main_path("data", "cache", "checksums.txt")
        checksums = load_checksums(checksums_file)

        cache = CacheManager(
            checksums=checksums,
            cache_dir=main_path("data", "cache"),
            checksums_file=checksums_file
        )

        # 4) Download and cache 1-minute OHLCV data for February 2025
        loader = BinanceDataLoader(
            fetcher=fetcher,
            cache=cache,
            start_year=2025,
            start_month=2,
            end_year=2025,
            end_month=2,
            interval="1m",
        )

        # results => {symbol: DataFrame containing OHLCV for each symbol}
        results = await loader.load_all_symbols(top_100_btc)

        # 5) Save the combined dataset to parquet for future reference
        parquet_outfile = main_path("data", "binance_1m_data.parquet")
        save_aggregated_parquet(results, parquet_outfile)

    # 6) Instantiate strategies (the data=None placeholders in your strategies will be replaced inside the Backtester)
    strategies = [
        (SmaCrossoverStrategy, {"init_cash": 10_000, "fees": 0.001}),
        (RsiBollingerStrategy, {"init_cash": 10_000, "fees": 0.001}),
        (VolumeSpikeBreakoutStrategy, {"init_cash": 10_000, "fees": 0.001}),
    ]

    # 7) Filter out any empty DataFrames (if, for example, data wasn't downloaded properly for certain symbols)
    results = {sym: df for sym, df in results.items() if not df.empty}

    # 8) Initialize the Backtester with the OHLCV data and the list of strategies
    backtester = Backtester(
        data_dict=results,  # Mapping symbol -> DataFrame
        strategies=strategies,
        results_dir=main_path("results"),  # Directory where outputs are saved
    )

    # 9) Run the backtests for each strategy on each symbol
    backtester.run_all()

    # 10) Save metrics to a CSV file
    metrics_csv = main_path("metrics.csv")
    backtester.save_metrics_to_csv(metrics_csv)

    # 11) Plot equity curves (using a log scale, sorting by final value, only top/bottom 5 lines) and save as HTML
    backtester.plot_equity_curves(
        use_log_scale=True,
        sort_by_final=True,
        top_bottom_n=5,
        save_html=True
    )

    # 12) Plot a heatmap for the "sharpe_ratio" metric across all strategies and symbols
    backtester.plot_performance_heatmap(
        metric="sharpe_ratio",
        template="plotly_white",
        range_color=(-10, 10),
        sort_symbols_by_mean=True,
    )

    # 13) (Optional) Generate an HTML report that includes the above charts
    report_html = main_path("report.html")
    backtester.generate_html_report(report_html)

    print("Backtest completed!")


if __name__ == "__main__":
    # Run the asynchronous main() function
    asyncio.run(main())
