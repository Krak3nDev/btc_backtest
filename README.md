# Multi-Strategy Cryptocurrency Trading Backtesting App

## Overview
This project implements a comprehensive backtesting app for trading strategies using VectorBT, focusing on 1-minute OHLCV data for 100 BTC trading pairs on Binance during February 2025.

## Project Structure
```
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # Project documentation
├── src/
│   └── btc_backtest/
│       ├── core/            # Core functionality
│       │   ├── backtester.py
│       │   ├── binance/     
│       │   │   ├── binance_client.py
│       │   │   ├── cache_manager.py
│       │   │   ├── fetcher.py
│       │   │   └── parser.py
│       │   ├── data_loader.py
│       │   └── metrics.py
│       ├── main.py          # Main execution script
│       └── strategies/      # Trading strategy implementations
│           ├── base.py
│           ├── rsi_bollinger.py
│           ├── sma_cross.py
│           └── volume_spike_breakout.py
└── tests/                   # Unit and integration tests
    ├── conftest.py
    ├── test_binance_fetcher.py
    ├── test_cache_manager.py
    ├── ...                  # Various test modules
```

## Prerequisites
- Python 3.12+
- Dependencies listed in `requirements.txt`

## Installation

### Standard Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Krak3nDev/btc_backtest.git
   cd btc_backtest
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # Or on Windows
   venv\Scripts\activate
   ```

3. Install the project in editable mode with development dependencies:
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```

### Using uv
```bash
# Create virtual environment and sync dependencies
uv sync

# Install the project in editable mode
uv pip install -e .
```

## Trading Strategies

### 1. SMA Crossover Strategy (Trend-Following)
#### Strategy Description
A classic trend-following approach that uses the crossover of two Simple Moving Averages (SMA) to generate trading signals. This strategy aims to capture sustained price movements by identifying potential trend changes.

#### Key Characteristics
- **Type**: Trend-Following
- **Indicator**: Simple Moving Averages (SMA)
- **Timeframe**: Suitable for multiple timeframes (daily, hourly)
- **Market Conditions**: Works best in trending markets

#### Detailed Parameters
- **Fast SMA Window**: 10 periods  
  - Represents short-term price momentum  
  - Quicker to react to price changes
- **Slow SMA Window**: 30 periods  
  - Represents long-term price trend  
  - Provides stability and reduces false signals

#### Signal Generation
- **Entry Signal**:  
  - **Long**: Fast SMA crosses above Slow SMA  
  - **Short**: Fast SMA crosses below Slow SMA
- **Exit Signal**:  
  - Close long position when Fast SMA crosses below Slow SMA  
  - Close short position when Fast SMA crosses above Slow SMA

---

### 2. RSI with Bollinger Bands Strategy (Mean Reversion)
#### Strategy Description
A sophisticated mean reversion strategy that combines the Relative Strength Index (RSI) with Bollinger Bands to identify potential price reversals and overbought/oversold conditions.

#### Key Characteristics
- **Type**: Mean Reversion
- **Indicators**: RSI, Bollinger Bands
- **Timeframe**: Versatile across different timeframes
- **Market Conditions**: Effective in range-bound markets

#### Detailed Parameters
- **RSI Parameters**:
  - Window: 14 periods
  - Oversold Threshold: <30
  - Overbought Threshold: >70
- **Bollinger Bands Parameters**:
  - Window: 20 periods
  - Standard Deviation: 2
  - Lower Band used for entry confirmation

#### Signal Generation
- **Entry Signal**:
  - RSI is below 30 (indicating oversold conditions)
  - Price bounces upward from the lower Bollinger Band
- **Exit Signal**:
  - RSI exceeds 70 (indicating overbought conditions)
  - Consider partial profit-taking or closing the position entirely

---

### 3. Volume Spike Breakout Strategy (Momentum)
#### Strategy Description
A momentum-based strategy that leverages volume spikes and price breakouts to capture significant market movements. The strategy focuses on detecting substantial trading activity combined with price action that breaks recent highs.

#### Key Characteristics
- **Type**: Momentum
- **Indicators**: Volume, Price Breakout
- **Timeframe**: Intraday to swing trading
- **Market Conditions**: Best suited for volatile, trending markets

#### Detailed Parameters
- **Volume Analysis**:
  - Window: 20 periods for the average volume calculation
  - Volume Spike Coefficient: 2.0 (current volume must be greater than 2x the average)
- **Breakout Parameters**:
  - Lookback Period: 10 bars to determine the recent local high
- **Exit Parameters**:
  - Lookback Period: 10 bars to determine the recent local low

#### Signal Generation
- **Entry Signal**:
  - A significant volume spike (current volume > 2x average volume)
  - Price breaks above the recent local high
- **Exit Signal**:
  - Price drops below the recent local low
  - This condition helps protect profits and limit losses

---

## Trading Strategy Performance Analysis

### SMA Crossover Strategy
- **Performance Observations**:
  - Most trading pairs show a declining equity curve and a Sharpe Ratio that is negative or near zero.
  - This indicates that the simple moving average crossover strategy performs poorly under current market conditions or requires additional signal filtering (e.g., using volatility or trend filters).
  - In sideways or highly volatile markets, the strategy often generates false signals and fails to hold profitable positions long enough.

### RSI Bollinger Strategy
- **Performance Observations**:
  - The equity curves for several pairs (e.g., ZILBTC, ONEBTC, VETBTC, ROSEBTC, etc.) exhibit significant portfolio value growth.
  - A positive Sharpe Ratio for many instruments suggests a better risk-to-reward balance.
  - High profitability may result from capturing strong trends after short-term drawdowns (RSI < 30) and benefiting from price rebounds.
  - There is a potential risk of over-optimization or anomalous market conditions, so it is advisable to test the strategy across different timeframes and periods.

### Volume Spike Breakout Strategy
- **Performance Observations**:
  - Most instruments display a gradual or sharp decline in portfolio value, as shown in the equity curves.
  - Low or negative Sharpe Ratios indicate instability and suboptimal parameter settings (e.g., volume spike coefficient, lookback periods).
  - A possible reason is that the market does not always sustain the momentum after a volume spike, or false breakouts occur.

### Overall Comparative Analysis
- **Strategy Ranking (Best to Worst)**:
  1. **RSI Bollinger Strategy**
  2. **Volume Spike Breakout Strategy**
  3. **SMA Crossover Strategy**

- **Performance Factors**:
  - **RSI Bollinger**:
    - Best at capturing market reversals
    - Strong risk management and adaptability to market conditions
  - **Volume Spike**:
    - Moderate momentum detection with some protection against total loss
  - **SMA Crossover**:
    - Least effective; highly vulnerable to market noise

---

## Usage
Run the main backtesting script:
```bash
python src/btc_backtest/main.py
```

