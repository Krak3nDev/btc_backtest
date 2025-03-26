import pytest
import pandas as pd
import vectorbt as vbt



def test_generate_signals_length(sma_crossover_strategy):
    """
    Check if generate_signals() returns two Series (entries, exits)
    with the same length as the input data.
    """
    entries, exits = sma_crossover_strategy.generate_signals()
    assert len(entries) == len(sma_crossover_strategy.data), (
        "The length of 'entries' does not match the DataFrame length."
    )
    assert len(exits) == len(sma_crossover_strategy.data), (
        "The length of 'exits' does not match the DataFrame length."
    )

def test_generate_signals_types(sma_crossover_strategy):
    """
    Check if 'entries' and 'exits' are boolean Series.
    """
    entries, exits = sma_crossover_strategy.generate_signals()
    assert entries.dtype == bool, "'entries' must be a boolean Series."
    assert exits.dtype == bool, "'exits' must be a boolean Series."

def test_no_signals_if_windows_are_inverted(sma_crossover_strategy):
    """
    If we deliberately invert the window sizes (fast_window > slow_window),
    we can check whether the strategy still returns signals or not.
    This might be an edge case: see if crossing logic is valid.
    """
    # For example, set fast_window = 40 (larger than slow_window = 30).
    sma_crossover_strategy.fast_window = 40
    sma_crossover_strategy.slow_window = 30

    entries, exits = sma_crossover_strategy.generate_signals()
    # Depending on your data, you might expect fewer or no signals.
    # Adjust the assertion if needed for your actual data set.
    # Here, we just assert no signals for demonstration:
    assert not entries.any(), "Expected no entries when fast_window > slow_window."
    assert not exits.any(), "Expected no exits when fast_window > slow_window."

def test_run_backtest_returns_portfolio(sma_crossover_strategy):
    """
    Verify that run_backtest() returns a vectorbt.Portfolio object
    and that it behaves as expected.
    """
    portfolio = sma_crossover_strategy.run_backtest()
    assert isinstance(portfolio, vbt.Portfolio), (
        "run_backtest() is expected to return a vbt.Portfolio instance."
    )

    # Check trades
    trades = portfolio.trades.records_readable
    assert isinstance(trades, pd.DataFrame), (
        "portfolio.trades.records_readable should be a DataFrame."
    )

    # Check final value
    final_value = portfolio.final_value()
    assert isinstance(final_value, float), "final_value() should return a float."
    assert final_value >= 0, "final_value() should not be negative."
