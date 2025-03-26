from pathlib import Path

import httpx
import pytest
import pandas as pd
import pytest_asyncio

from btc_backtest.core.binance.binance_client import PairsFetcher
from btc_backtest.core.binance.cache_manager import CacheManager
from btc_backtest.core.binance.fetcher import BinanceFetcher
from btc_backtest.strategies.base import StrategyBase
from btc_backtest.strategies.rsi_bollinger import RsiBollingerStrategy
from btc_backtest.strategies.sma_cross import SmaCrossoverStrategy
from btc_backtest.strategies.volume_spike_breakout import VolumeSpikeBreakoutStrategy


@pytest.fixture
def mock_data():
    data = {
        "close": [
            100, 101, 102, 99, 98, 97, 96, 97, 98, 105, 110, 112,
            115, 113, 111, 109, 108, 107, 105, 103, 104, 106, 107, 108,
        ],
        "open": [100, 100, 101, 98, 98, 98, 96, 96, 98, 103, 109, 110, 112, 112, 110, 108, 108, 106, 104, 103, 102, 105, 106, 107],
        "high": [101, 102, 103, 100, 99, 98, 97, 98, 99, 106, 111, 113, 116, 114, 112, 110, 110, 108, 106, 105, 105, 107, 108, 109],
        "low":  [99, 99, 100, 98, 97, 96, 95, 96, 97, 102, 109, 110, 114, 112, 110, 107, 107, 105, 104, 102, 101, 104, 106, 106],
        "volume": [
            1000, 1200, 1100, 900, 950, 1000, 1050, 980, 1000, 1500,
            2000, 2200, 2100, 1900, 1800, 1750, 1600, 1650, 1400, 1300,
            1250, 1300, 1350, 1400,
        ],
    }
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def base_strategy(mock_data):
    strategy = StrategyBase(
        data=mock_data,
        init_cash=10_000,
        fees=0.001,
    )
    return strategy


@pytest.fixture
def rsi_bb_strategy(mock_data):
    strategy = RsiBollingerStrategy(
        data=mock_data,
        init_cash=10_000,
        fees=0.001,
        rsi_window=14,
        bb_window=20,
        rsi_low_level=30.0,
        rsi_high_level=70.0,
    )
    return strategy



@pytest.fixture
def sma_crossover_strategy(mock_data):
    strategy = SmaCrossoverStrategy(
        data=mock_data,
        init_cash=10_000,
        fees=0.001,
        fast_window=10,
        slow_window=30,
    )
    return strategy

@pytest.fixture
def volume_breakout_strategy(mock_data):
    strategy = VolumeSpikeBreakoutStrategy(
        data=mock_data,
        init_cash=10_000,
        fees=0.001,
        volume_window=5,
        volume_spike_coef=2.0,
        breakout_lookback=3,
        exit_lookback=3,
    )
    return strategy

@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture
def pairs_fetcher(client: httpx.AsyncClient):
    return PairsFetcher(client)

@pytest.fixture
def binance_fetcher(client: httpx.AsyncClient):
    return BinanceFetcher(client)

@pytest.fixture
def checksums_file(tmp_path: Path) -> Path:
    return tmp_path / "checksums.txt"

@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cache"
    d.mkdir(exist_ok=True)
    return d

@pytest.fixture
def cache_manager(checksums_file: Path, cache_dir: Path) -> CacheManager:
    return CacheManager(
        checksums={},
        cache_dir=str(cache_dir),
        checksums_file=str(checksums_file),
    )