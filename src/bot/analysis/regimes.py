"""Marktphasen (Bull/Bear) und Kennzahlen pro Phase.

Definition: Tag t ist «bull», wenn Close(t−1) > SMA200(t−1), sonst «bear».
WARUM t−1: Die Phase eines Tages ist so schon zu Beginn des Tages bekannt
(kein Look-Ahead). Die Phase dient nur der Auswertung, nicht als Handelssignal.
"""

import numpy as np
import pandas as pd

from bot.analysis.metrics import daily_risk_free, max_drawdown, sharpe_ratio
from bot.backtest.engine import BacktestResult
from bot.strategies.indicators import sma

REGIMES = ["bull", "bear"]


def classify_regimes(df: pd.DataFrame, settings: dict) -> pd.Series:
    """Gibt pro Tag "bull" oder "bear" zurück (NaN, solange der SMA noch nicht berechnet ist)."""
    ma = sma(df["close"], settings["regime_ma_days"])
    prev_close, prev_ma = df["close"].shift(1), ma.shift(1)
    regime = pd.Series(np.where(prev_close > prev_ma, "bull", "bear"), index=df.index, name="regime")
    return regime.where(prev_ma.notna())


def regime_metrics(result: BacktestResult, regimes: pd.Series, settings: dict) -> dict[str, dict]:
    """Kennzahlen pro Marktphase: Anteil Tage, Rendite, Sharpe, Max Drawdown.

    WARUM so berechnet: Die Tage einer Phase sind nicht zusammenhängend. Ihre
    Netto-Renditen werden aneinandergereiht, als gäbe es nur diese Tage.
    Rendite und Drawdown beziehen sich auf diese verkettete Equity-Kurve.
    """
    daily = result.daily
    phase = regimes.reindex(daily.index)
    rf = daily_risk_free(settings)
    periods = settings["annualization_days"]
    out = {}
    for name in REGIMES:
        net = daily.loc[phase == name, "net_return"]
        if net.empty:
            out[name] = {"n_days": 0, "share_days": 0.0}
            continue
        equity = (1 + net).cumprod()
        out[name] = {
            "n_days": len(net),
            "share_days": len(net) / len(daily),
            "total_return": float(equity.iloc[-1] - 1),
            "sharpe": sharpe_ratio(net, rf, periods),
            "max_drawdown": max_drawdown(equity)["max_drawdown"],
        }
    return out
