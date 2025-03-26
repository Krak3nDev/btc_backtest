import pandas as pd

from btc_backtest.strategies.base import StrategyBase


class VolumeSpikeBreakoutStrategy(StrategyBase):
    """
    A volume-spike breakout strategy:
    - Entry when a "volume spike" (current_volume >> average_volume) occurs
      along with a breakout above a recent local high.
    - Exit when price falls below a certain N-period local low.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        init_cash: float = 10_000,
        fees: float = 0.001,
        volume_window: int = 20,
        volume_spike_coef: float = 2.0,
        breakout_lookback: int = 10,
        exit_lookback: int = 10,
    ) -> None:
        """
        Initialize the VolumeSpikeBreakoutStrategy.

        Args:
            data (pd.DataFrame): OHLCV DataFrame (must contain 'close' and 'volume' columns).
            init_cash (float): Initial capital.
            fees (float): Commission in relative terms (e.g., 0.001 means 0.1%).
            volume_window (int): Rolling window size for average volume calculation.
            volume_spike_coef (float): Multiplier for detecting a volume spike.
                For instance, 2.0 => current volume > 2 * average volume.
            breakout_lookback (int): Number of bars to consider when checking for a local high breakout.
            exit_lookback (int): Number of bars to consider when checking a local low for exit conditions.
        """
        super().__init__(data, init_cash, fees)
        self.volume_window = volume_window
        self.volume_spike_coef = volume_spike_coef
        self.breakout_lookback = breakout_lookback
        self.exit_lookback = exit_lookback

    def generate_signals(self) -> tuple[pd.Series, pd.Series]:
        """
        Generate entry and exit signals based on volume spikes and breakouts.

        Returns:
            tuple[pd.Series, pd.Series]:
                A tuple (entries, exits), each is a boolean Series indexed
                by the same dates as self.data. `True` indicates a signal on that bar.

        Raises:
            ValueError: If 'close' or 'volume' columns are missing in the DataFrame.
        """
        # Ensure required columns exist
        if "close" not in self.data or "volume" not in self.data:
            raise ValueError("DataFrame must contain 'close' and 'volume' columns.")

        close = self.data["close"]
        volume = self.data["volume"]

        # 1. Detect volume spike: current volume > (rolling_mean_volume * volume_spike_coef)
        rolling_mean_vol = volume.rolling(self.volume_window).mean()
        volume_spike = volume > (rolling_mean_vol * self.volume_spike_coef)

        # 2. Check for breakout above the recent local high over the last breakout_lookback bars
        recent_high = close.rolling(self.breakout_lookback).max()
        # We consider a breakout if the current close crosses above the recent high.
        # Example logic: current close > shifted recent high, while
        # the previous close <= that shifted high (indicating a fresh breakout).
        breakout = (close > recent_high.shift(1)) & (close.shift(1) <= recent_high.shift(1))

        # Entry signal: volume spike + breakout occur simultaneously
        entries = volume_spike & breakout

        # 3. Exit signal: price falls below the local N-bar low
        recent_low = close.rolling(self.exit_lookback).min()
        exits = close < recent_low.shift(1)

        # Fill NaNs with False to avoid any NaN-based issues
        return entries.fillna(False), exits.fillna(False)
