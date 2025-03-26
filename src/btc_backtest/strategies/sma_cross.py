import pandas as pd

from btc_backtest.strategies.base import StrategyBase


class SmaCrossoverStrategy(StrategyBase):
    """
    A simple SMA crossover strategy:
    - Entry when a 'fast' SMA crosses above a 'slow' SMA.
    - Exit when the fast SMA crosses below the slow SMA.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        init_cash: float = 10_000,
        fees: float = 0.001,
        fast_window: int = 10,
        slow_window: int = 30,
    ) -> None:
        """
        Initialize the SmaCrossoverStrategy.

        Args:
            data (pd.DataFrame): OHLCV data (must have a 'close' column at minimum).
            init_cash (float): Initial trading capital.
            fees (float): Commission per trade in relative terms (e.g., 0.001 = 0.1%).
            fast_window (int): The window size of the fast-moving SMA.
            slow_window (int): The window size of the slow-moving SMA.
        """
        super().__init__(data, init_cash, fees)
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self) -> tuple[pd.Series, pd.Series]:
        """
        Generate entry/exit signals based on a fast SMA vs. a slow SMA.

        Returns:
            tuple[pd.Series, pd.Series]:
                A tuple of (entries, exits), each is a boolean Series indexed by the same
                dates as `self.data`. `True` indicates entering (entries) or exiting (exits) on that bar.
        """
        close = self.data["close"]

        # Compute moving averages
        sma_fast = close.rolling(self.fast_window).mean()
        sma_slow = close.rolling(self.slow_window).mean()

        # Entry when fast SMA crosses above slow SMA
        entries = (sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))

        # Exit when fast SMA crosses below slow SMA
        exits = (sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))

        return entries, exits