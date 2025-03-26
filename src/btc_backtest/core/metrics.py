# project/core/metrics.py

import vectorbt as vbt
from ccxt.base.types import TypedDict


class Metrics(TypedDict):
    total_return: float
    winrate: float
    expectancy: float


def compute_custom_metrics(portfolio: vbt.Portfolio) -> Metrics:
    """
    Обчислює додаткові метрики (наприклад, winrate, expectancy).
    Повертає словник { "winrate": ..., "expectancy": ..., "total_return": ... }
    """
    # Трейди
    trades = portfolio.trades.records_readable

    # total_return (%):
    # VectorBT має портфельні методи, наприклад, pf.total_return()
    # але для прикладу можемо взяти:
    val_ser = portfolio.value()
    # Якщо треба перший і останній елемент “по позиції”:
    total_return = (val_ser.iloc[-1] / val_ser.iloc[0] - 1) * 100

    # Якщо у DataFrame трейдів немає колонки 'PnL', повертаємо 0 для winrate та expectancy
    if "PnL" not in trades.columns:
        return Metrics(total_return=float(total_return), winrate=0.0, expectancy=0.0)

    wins = trades[trades["PnL"] > 0]
    losses = trades[trades["PnL"] <= 0]

    total_trades = len(trades)
    if total_trades == 0:
        winrate = 0.0
        expectancy = 0.0
    else:
        winrate = len(wins) / total_trades
        avg_win = wins["PnL"].mean() if len(wins) > 0 else 0.0
        avg_loss = losses["PnL"].mean() if len(losses) > 0 else 0.0
        expectancy = (winrate * avg_win) + ((1 - winrate) * avg_loss)

    return Metrics(
        total_return= float(total_return),
        winrate=float(winrate),
        expectancy=float(expectancy),
    )
