import pytest
import pandas as pd
import numpy as np
import vectorbt as vbt

from typing import Tuple
from btc_backtest.strategies.base import StrategyBase, compute_time_in_position, MetricsDict



def test_compute_time_in_position_no_trades(mock_data: pd.DataFrame):
    """
    If there are no orders in the portfolio,
    compute_time_in_position should return 0.
    """
    # Create an empty Portfolio (no trades) using vectorbt
    pf = vbt.Portfolio.from_signals(
        close=mock_data["close"],
        entries=pd.Series(False, index=mock_data.index),
        exits=pd.Series(False, index=mock_data.index),
        init_cash=10000,
        fees=0.001,
        freq="1Min"
    )

    assert len(pf.orders.records) == 0, "No orders should exist"
    pos_time = compute_time_in_position(pf)
    assert pos_time == 0.0, "Time in position should be zero if no trades occurred."


def test_compute_time_in_position_with_trades(mock_data: pd.DataFrame):
    """
    Checks if compute_time_in_position returns a reasonable
    value when there are some trades.
    """
    # Let entries be True at bar 2 and bar 5, exits at bar 3 and bar 7, for instance
    entries = pd.Series(False, index=mock_data.index)
    exits = pd.Series(False, index=mock_data.index)
    entries.iloc[[2, 5]] = True
    exits.iloc[[3, 7]] = True

    pf = vbt.Portfolio.from_signals(
        close=mock_data["close"],
        entries=entries,
        exits=exits,
        init_cash=10000,
        fees=0.001,
        freq="1Min"
    )
    # Now let's see how long we were in position
    pos_time = compute_time_in_position(pf)
    # We expect at least 1 bar in position between 2 and 3, and 2 bars between 5 and 7, etc.
    # It's enough to check it's > 0 and <= 100
    assert 0 < pos_time <= 100, "Time in position must be within (0,100] for partial trades."


def test_strategy_base_not_implemented(mock_data: pd.DataFrame):
    """
    If we instantiate StrategyBase directly and call generate_signals(),
    it should raise NotImplementedError.
    """
    strat = StrategyBase(data=mock_data)
    with pytest.raises(NotImplementedError):
        strat.generate_signals()


def test_strategy_base_run_backtest_missing_close():
    """
    If 'close' column is missing, run_backtest() should raise a KeyError or similar error
    when accessing self.data["close"].
    """
    # DataFrame without 'close' column
    df = pd.DataFrame({
        "open": [1, 2, 3],
        "high": [2, 3, 4],
        "low": [1, 1, 2],
        "volume": [100, 200, 300],
    })
    strat = StrategyBase(data=df)
    with pytest.raises(KeyError):
        strat.run_backtest()


class TestStrategy(StrategyBase):
    """
    A simple test strategy that always enters on the first bar and exits on the last bar.
    """
    def generate_signals(self) -> Tuple[pd.Series, pd.Series]:
        entries = pd.Series(False, index=self.data.index)
        exits = pd.Series(False, index=self.data.index)

        if len(self.data) > 1:
            entries.iloc[0] = True
            exits.iloc[-1] = True

        return entries, exits


def test_test_strategy_run_backtest(base_strategy: StrategyBase, mock_data: pd.DataFrame):
    """
    Verify that a subclass of StrategyBase with an actual generate_signals()
    can run a backtest without errors and produce expected metrics.
    """
    strat = TestStrategy(data=mock_data)
    pf = strat.run_backtest()

    # We expect exactly 2 orders (1 buy, 1 sell)
    assert len(pf.orders.records) == 2, "There should be 1 entry and 1 exit order."

    metrics = strat.get_metrics()
    assert isinstance(metrics, dict), "Metrics should be a dictionary-like object."
    assert "stats" in metrics, "'stats' should be in the metrics."
    assert "sharpe_ratio" in metrics, "'sharpe_ratio' should be in the metrics."
    assert "drawdown" in metrics, "'drawdown' should be in the metrics."
    assert "exposure" in metrics, "'exposure' should be in the metrics."

    # For this trivial strategy, we can at least check we have a positive or negative float for Sharpe Ratio
    assert isinstance(metrics["sharpe_ratio"], (float, pd.Series)), "Sharpe ratio must be a float or a series."
    assert isinstance(metrics["drawdown"], (float, pd.Series)), "Drawdown must be a float or a series."
    assert 0 <= metrics["exposure"] <= 100, "Exposure should be between 0 and 100%."
