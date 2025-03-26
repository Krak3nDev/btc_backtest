import pytest
import httpx

from httpx import HTTPStatusError, RequestError

from btc_backtest.core.binance.binance_client import PairsFetcher


@pytest.mark.asyncio
async def test_get_top_pairs_btc_integration(pairs_fetcher: PairsFetcher):
    """
    Integration test for PairsFetcher.get_top_pairs with quote='BTC'.
    Fetches data from Binance in real-time.
    """


    # We ask for top 5 pairs with BTC quote
    top_pairs = await pairs_fetcher.get_top_pairs(quote="BTC", limit=5)

    # Basic checks
    assert isinstance(top_pairs, list), "Result should be a list."
    assert len(top_pairs) <= 5, "Result should have length up to 5."

    # Each pair should end with 'BTC' (e.g., 'ETHBTC')
    for pair in top_pairs:
        assert pair.endswith("BTC"), f"Pair '{pair}' does not end with 'BTC'."

@pytest.mark.asyncio
async def test_get_top_pairs_usdt_integration(pairs_fetcher: PairsFetcher):
    """
    Integration test for PairsFetcher.get_top_pairs with quote='USDT'.
    This verifies we can request other quotes as well.
    """


    # Let’s just take 3 for demonstration
    top_pairs = await pairs_fetcher.get_top_pairs(quote="USDT", limit=3)

    assert isinstance(top_pairs, list), "Result should be a list."
    assert len(top_pairs) <= 3, "Should retrieve up to 3 pairs."

    # Each pair should end with 'USDT' (e.g., 'BTCUSDT')
    for pair in top_pairs:
        assert pair.endswith("USDT"), f"Pair '{pair}' does not end with 'USDT'."


@pytest.mark.asyncio
async def test_get_top_pairs_handles_retry(pairs_fetcher: PairsFetcher):
    """
    If the server is temporarily unavailable, tenacity should retry.
    We can't easily force Binance to fail, but this test at least ensures
    no exception is raised under normal conditions, and the retry logic
    won't break the flow.
    """


    # We'll call get_top_pairs normally. If the API fails temporarily,
    # tenacity retry logic should handle it up to 5 attempts.
    # If it's consistently down, the test might fail after 5 tries.
    try:
        top_pairs = await pairs_fetcher.get_top_pairs(quote="BTC", limit=2)
        # If no exception was raised, we can do a basic assertion
        assert isinstance(top_pairs, list), "Result should be a list."
    except (RequestError, HTTPStatusError) as e:
        pytest.fail(f"Request failed after retries: {e}")
