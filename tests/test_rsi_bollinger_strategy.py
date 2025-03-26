import pandas as pd
import vectorbt as vbt

def test_generate_signals_length(rsi_bb_strategy):
    """
    Check if generate_signals() returns two Series (entries, exits)
    with the same length as the input data.
    """
    entries, exits = rsi_bb_strategy.generate_signals()
    assert len(entries) == len(rsi_bb_strategy.data), (
        "The length of 'entries' does not match the DataFrame length."
    )
    assert len(exits) == len(rsi_bb_strategy.data), (
        "The length of 'exits' does not match the DataFrame length."
    )

def test_generate_signals_types(rsi_bb_strategy):
    """
    Check if 'entries' and 'exits' are boolean Series.
    """
    entries, exits = rsi_bb_strategy.generate_signals()
    assert entries.dtype == bool, "'entries' must be a boolean Series."
    assert exits.dtype == bool, "'exits' must be a boolean Series."

def test_no_entry_if_rsi_not_oversold(rsi_bb_strategy):
    """
    Basic RSI condition check:
    If we artificially lower the RSI 'low' level, the strategy
    should not generate any entry signals.
    """
    # Set the oversold threshold so low that RSI is always above it.
    rsi_bb_strategy.rsi_low_level = 10.0
    entries, _ = rsi_bb_strategy.generate_signals()
    # Verify that there are no entry signals.
    assert not entries.any(), (
        "There should be no entry signals if RSI's oversold threshold is set too low."
    )

def test_run_backtest_returns_portfolio(rsi_bb_strategy):
    """
    Verify that run_backtest() returns a vectorbt.Portfolio object.
    Check a few basic attributes or methods of the returned portfolio.
    """
    portfolio = rsi_bb_strategy.run_backtest()
    # Check that we actually get a vbt.Portfolio instance
    assert isinstance(portfolio, vbt.Portfolio), (
        "run_backtest() is expected to return a vbt.Portfolio instance."
    )

    # Check the trades records
    trades = portfolio.trades.records_readable
    assert isinstance(trades, pd.DataFrame), (
        "pf.trades.records_readable should be a DataFrame."
    )
    # The trades DataFrame could have zero or more rows, but it shouldn't be None

    # Check the final value
    final_value = portfolio.final_value()
    assert isinstance(final_value, float), "pf.final_value() should return a float."
    assert final_value >= 0, "pf.final_value() cannot be negative."
