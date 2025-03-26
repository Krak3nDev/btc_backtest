from typing import TypedDict, Union, Tuple

import numpy as np
import pandas as pd
import vectorbt as vbt


class MetricsDict(TypedDict):
    """
    A typed dictionary for storing basic metrics of a strategy/portfolio.

    Attributes:
        stats (pd.Series | pd.DataFrame):
            A summary of stats from vectorbt's Portfolio.stats().
        sharpe_ratio (float | pd.Series):
            Sharpe ratio of the portfolio.
        drawdown (float | pd.Series):
            Maximum drawdown of the portfolio.
        exposure (float | pd.Series):
            Percentage of bars when the portfolio was in a position.
    """
    stats: pd.Series | pd.DataFrame
    sharpe_ratio: float | pd.Series
    drawdown: float | pd.Series
    exposure: float | pd.Series


def compute_time_in_position(pf: vbt.Portfolio) -> float:
    """
    Calculate the percentage of bars during which the portfolio was in a position.

    This function analyzes the records of orders placed by the portfolio
    and determines for each bar whether the portfolio was holding any coins.

    Args:
        pf (vbt.Portfolio): A vectorbt Portfolio object.

    Returns:
        float: The percentage of bars (0 to 100) where the position size > 0.
    """
    orders_df = pf.orders.records.copy()
    # Sort by bar index ("idx")
    orders_df.sort_values("idx", inplace=True)

    n_bars = len(pf.wrapper.index)
    in_pos = np.zeros(n_bars, dtype=bool)

    pos_state = 0.0  # How many coins are currently held
    last_idx = 0     # The last bar index we processed

    for _, row in orders_df.iterrows():
        current_idx = int(row["idx"])

        # Mark as "in position" for the range [last_idx, current_idx),
        # if pos_state > 0 indicates we were in a position
        if pos_state > 0:
            in_pos[last_idx:current_idx] = True

        # Update the pos_state (number of coins)
        # side=0 => buy => add to position, side=1 => sell => subtract from position
        if row["side"] == 0:
            pos_state += row["size"]
        else:
            pos_state -= row["size"]

        # Move last_idx pointer
        last_idx = current_idx

    # If still in position after the last order, fill the rest
    if pos_state > 0:
        in_pos[last_idx:] = True

    # Return the percentage of bars where we were in position
    return in_pos.mean() * 100.0


class StrategyBase:
    """
    A base class representing a trading strategy with vectorbt.

    Subclasses should implement the `generate_signals()` method
    to produce entry/exit signals.

    Args:
        data (pd.DataFrame): A DataFrame containing at least ['open','high','low','close','volume'] columns.
        init_cash (float): The initial capital allocated for this strategy.
        fees (float): Commission per trade in relative terms (e.g. 0.001 = 0.1%).
    """
    def __init__(
        self,
        data: pd.DataFrame,
        init_cash: float = 10_000,
        fees: float = 0.001
    ) -> None:
        self.data: pd.DataFrame = data
        self.init_cash: float = init_cash
        self.fees: float = fees
        self.pf: Union[vbt.Portfolio, None] = None  # Will store the Portfolio after running backtest

    def generate_signals(self) -> tuple[pd.Series, pd.Series]:
        """
        Generate boolean Series for entries and exits (long-only signals).

        Returns:
            Tuple[pd.Series, pd.Series]: A tuple (entries, exits), each is a boolean Series
            indexed by the same dates as self.data. `True` indicates enter/exit on that bar.

        Raises:
            NotImplementedError: If the method is not overridden in a subclass.
        """
        raise NotImplementedError("Please override generate_signals() in a subclass.")

    def run_backtest(self) -> vbt.Portfolio:
        """
        Run the backtest by calling vectorbt.Portfolio.from_signals().

        - It uses the 'close' prices from self.data.
        - The entry/exit signals come from generate_signals().
        - Stores the resulting Portfolio in self.pf.

        Returns:
            vbt.Portfolio: The vectorbt Portfolio object with all trade records and stats.

        Raises:
            ValueError: If the 'close' column is missing or signals shape is invalid.
        """
        close = self.data["close"]
        entries, exits = self.generate_signals()

        self.pf = vbt.Portfolio.from_signals(
            close=close,
            entries=entries,
            exits=exits,
            init_cash=self.init_cash,
            fees=self.fees,
            slippage=0.0,
            freq="1Min",  # we assume 1-minute data
        )
        return self.pf

    def get_metrics(self) -> MetricsDict:
        """
        Retrieve the basic metrics of the strategy, including sharpe ratio, max drawdown,
        time in position, and vectorbt's stats().

        Returns:
            MetricsDict: A dictionary with keys: stats, sharpe_ratio, drawdown, exposure

        Raises:
            ValueError: If run_backtest() has not been called yet.
        """
        if self.pf is None:
            raise ValueError("Please call run_backtest() before fetching metrics.")

        stats = self.pf.stats()
        exposure_percent = compute_time_in_position(self.pf)

        return MetricsDict(
            stats=stats,
            sharpe_ratio=self.pf.sharpe_ratio(freq="1Min"),
            drawdown=self.pf.max_drawdown(),
            exposure=exposure_percent,
        )
