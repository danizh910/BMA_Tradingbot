"""Technische Indikatoren. Alle sind kausal: Wert t nutzt nur Daten bis und mit t.

WARUM eigene Implementierung: Jede Formel ist sichtbar und wird gegen
von Hand gerechnete Werte getestet (tests/test_indicators.py).
"""

import numpy as np
import pandas as pd

from bot.data.validate import true_range


def sma(series: pd.Series, window: int) -> pd.Series:
    """Einfacher gleitender Durchschnitt der letzten `window` Werte (kausal, center=False).

    Die ersten window−1 Werte sind NaN (zu wenig Daten).
    """
    return series.rolling(window, center=False).mean()


def roc(close: pd.Series, period: int) -> pd.Series:
    """Rate of Change: ROC_t = Close_t / Close_(t−period) − 1."""
    return close / close.shift(period) - 1


def wilder_smooth(values: pd.Series, period: int) -> pd.Series:
    """Glättung nach Wilder (RMA).

    Startwert = einfacher Mittelwert der ersten `period` gültigen Werte,
    danach rekursiv: avg_t = (avg_(t−1) × (period − 1) + x_t) / period.
    WARUM Schleife statt ewm(): pandas' ewm(adjust=False) startet mit dem ersten
    Einzelwert statt mit dem Mittelwert. Das weicht von Wilders Definition ab.
    """
    x = values.tolist()
    out = [np.nan] * len(x)
    first = next((i for i, v in enumerate(x) if not np.isnan(v)), None)
    if first is None or first + period > len(x):
        return pd.Series(out, index=values.index)
    seed_end = first + period - 1
    avg = float(np.mean(x[first:seed_end + 1]))
    out[seed_end] = avg
    for i in range(seed_end + 1, len(x)):
        avg = (avg * (period - 1) + x[i]) / period
        out[i] = avg
    return pd.Series(out, index=values.index)


def rsi(close: pd.Series, period: int) -> pd.Series:
    """Relative Strength Index nach Wilder.

    Δ_t = Close_t − Close_(t−1); Gewinn = max(Δ, 0), Verlust = max(−Δ, 0)
    RS = WilderAvg(Gewinn) / WilderAvg(Verlust); RSI = 100 − 100 / (1 + RS)
    Division durch 0: nur Gewinne → RSI 100; keine Bewegung → RSI 50.
    """
    delta = close.diff()
    avg_gain = wilder_smooth(delta.clip(lower=0), period)
    avg_loss = wilder_smooth((-delta).clip(lower=0), period)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss
        values = 100 - 100 / (1 + rs)
    values = values.where(avg_loss != 0, 100.0)
    values = values.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
    return values.where(avg_gain.notna())


def atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Average True Range nach Wilder.

    True Range_t = max(High − Low, |High − Close_(t−1)|, |Low − Close_(t−1)|);
    am ersten Tag (kein Vortag) = High − Low. ATR = WilderAvg(True Range, period).
    """
    return wilder_smooth(true_range(df), period)
