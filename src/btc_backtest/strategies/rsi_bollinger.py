import pandas as pd
import ta

from btc_backtest.strategies.base import StrategyBase


class RsiBollingerStrategy(StrategyBase):
    """
    This strategy combines RSI and Bollinger Bands:
    - Entry when RSI < rsi_low_level (oversold) AND price bounces upward from the Bollinger lower band.
    - Exit when RSI > rsi_high_level (overbought).
    """

    def __init__(
        self,
        data: pd.DataFrame,
        init_cash: float = 10_000,
        fees: float = 0.001,
        rsi_window: int = 14,
        bb_window: int = 20,
        rsi_low_level: float = 30.0,
        rsi_high_level: float = 70.0,
    ) -> None:
        """
        Initialize the RsiBollingerStrategy.

        Args:
            data (pd.DataFrame): OHLCV data (minimally needs a 'close' column).
            init_cash (float): Initial trading capital.
            fees (float): Commission per trade in relative terms (e.g. 0.001 = 0.1%).
            rsi_window (int): Window size for the RSI calculation.
            bb_window (int): Window size for the Bollinger Bands calculation.
            rsi_low_level (float): RSI threshold below which we consider the market oversold.
            rsi_high_level (float): RSI threshold above which we consider the market overbought.
        """
        super().__init__(data, init_cash, fees)
        self.rsi_window = rsi_window
        self.bb_window = bb_window
        self.rsi_low_level = rsi_low_level
        self.rsi_high_level = rsi_high_level

    def generate_signals(self) -> tuple[pd.Series, pd.Series]:
        """
        Generate entry and exit signals based on RSI and Bollinger Bands.

        Logic:
            - entries:
                RSI < rsi_low_level (oversold condition),
                AND the price has just crossed above the lower Bollinger band
                (i.e., a "bounce" from the lower band).
            - exits:
                RSI > rsi_high_level (overbought condition).

        Returns:
            tuple[pd.Series, pd.Series]:
                A tuple of (entries, exits) where each is a boolean Series
                aligned with the DataFrame's index.
        """
        close = self.data["close"]

        # --- Compute RSI ---
        rsi_series = ta.momentum.RSIIndicator(close=close, window=self.rsi_window).rsi()

        # --- Compute Bollinger Bands ---
        bb = ta.volatility.BollingerBands(close=close, window=self.bb_window, window_dev=2)
        lower_band = bb.bollinger_lband()
        # If needed, you could also use:
        #   middle_band = bb.bollinger_mavg()
        #   upper_band = bb.bollinger_hband()

        # Oversold condition (RSI < low level)
        rsi_oversold = rsi_series < self.rsi_low_level

        # "Bounce" from lower band: current close crosses above the lower band
        bounced_from_lower = (close > lower_band) & (close.shift(1) <= lower_band.shift(1))

        # Entry: oversold + bounce
        entries = rsi_oversold & bounced_from_lower

        # Exit: overbought (RSI > high level)
        exits = rsi_series > self.rsi_high_level

        return entries, exits
