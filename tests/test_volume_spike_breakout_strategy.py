import pytest
import pandas as pd
import vectorbt as vbt

from btc_backtest.strategies.volume_spike_breakout import VolumeSpikeBreakoutStrategy


def test_generate_signals_length(volume_breakout_strategy):
    """
    Check that generate_signals() returns two Series (entries, exits)
    with the same length as the strategy's DataFrame.
    """
    entries, exits = volume_breakout_strategy.generate_signals()
    assert len(entries) == len(volume_breakout_strategy.data), (
        "Entries length must match data length."
    )
    assert len(exits) == len(volume_breakout_strategy.data), (
        "Exits length must match data length."
    )

def test_generate_signals_types(volume_breakout_strategy):
    """
    Check that both entries and exits are boolean Series.
    """
    entries, exits = volume_breakout_strategy.generate_signals()
    assert entries.dtype == bool, "Entries should be a boolean Series."
    assert exits.dtype == bool, "Exits should be a boolean Series."

def test_missing_columns():
    """
    If 'close' or 'volume' columns are missing,
    the strategy should raise a ValueError.
    """
    # Missing 'volume' column
    df_missing_volume = pd.DataFrame({"close": [100, 101, 102]})
    # Missing 'close' column
    df_missing_close = pd.DataFrame({"volume": [1000, 2000, 3000]})

    with pytest.raises(ValueError, match="must contain 'close' and 'volume'"):
        VolumeSpikeBreakoutStrategy(data=df_missing_volume).generate_signals()

    with pytest.raises(ValueError, match="must contain 'close' and 'volume'"):
        VolumeSpikeBreakoutStrategy(data=df_missing_close).generate_signals()

def test_volume_spike_coefficient(volume_breakout_strategy):
    """
    Check that increasing volume_spike_coef significantly reduces (or eliminates)
    entry signals due to the stricter volume spike requirement.
    """
    # Generate signals with default spike coefficient
    entries_default, _ = volume_breakout_strategy.generate_signals()
    count_default = entries_default.sum()

    # Make the spike coefficient extremely high, so no spike occurs
    volume_breakout_strategy.volume_spike_coef = 100.0
    entries_high_coef, _ = volume_breakout_strategy.generate_signals()
    count_high_coef = entries_high_coef.sum()

    # Expect fewer (or zero) entries with a much higher spike coefficient
    assert count_high_coef <= count_default, (
        "Raising volume_spike_coef should produce fewer or no entry signals."
    )

def test_run_backtest_returns_portfolio(volume_breakout_strategy):
    """
    Ensure run_backtest() returns a vbt.Portfolio object,
    and check some basic attributes.
    """
    pf = volume_breakout_strategy.run_backtest()
    assert isinstance(pf, vbt.Portfolio), (
        "run_backtest() is expected to return a vectorbt.Portfolio instance."
    )

    # Check trades
    trades = pf.trades.records_readable
    assert isinstance(trades, pd.DataFrame), (
        "Portfolio trades should be accessible as a DataFrame."
    )

    # Check final value
    final_val = pf.final_value()
    assert isinstance(final_val, float), "final_value() should return a float."
    assert final_val >= 0, "final_value() should not be negative."
