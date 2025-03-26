import pytest

from btc_backtest.core.binance.fetcher import BinanceFetcher


@pytest.mark.asyncio
async def test_fetch_kline_zip_real_ok(binance_fetcher: BinanceFetcher):
    """
    Integration test hitting the real Binance endpoint.
    We try to fetch a known (likely existing) dataset:
      symbol='BTCUSDT', interval='1d', year=2023, month=1
    If it exists, we should get non-empty bytes and NOT b"404_NOT_FOUND".
    """
    content = await binance_fetcher.fetch_kline_zip("BTCUSDT", "1d", 2023, 1)
    assert content != b"404_NOT_FOUND", (
        "We expected real data from Binance for BTCUSDT 1d 2023-01; got 404_NOT_FOUND instead. "
        "Either data doesn't exist or there's a network issue."
    )
    assert len(content) > 0, "Expected non-empty ZIP content."


@pytest.mark.asyncio
async def test_fetch_kline_zip_real_404(binance_fetcher: BinanceFetcher):
    """
    Integration test hitting the real Binance endpoint for a resource
    that doesn't exist. We expect b"404_NOT_FOUND".
    Try a combination that likely doesn't exist on Binance. E.g. an extremely old date,
    or a random symbol. Adjust as needed if this test fails.
    """
    content = await binance_fetcher.fetch_kline_zip("NO_SUCH_SYMBOL", "1d", 1999, 12)
    assert content == b"404_NOT_FOUND", (
        "Expected 404_NOT_FOUND for a non-existent symbol/year/month, "
        "but got some other response."
    )
