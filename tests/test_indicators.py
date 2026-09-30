"""Tests der Indikatoren gegen von Hand berechnete Mini-Reihen (Periode 3)."""

import numpy as np
import pandas as pd
import pytest

from bot.strategies.indicators import atr, roc, rsi, sma, wilder_smooth


def idx(n: int) -> pd.DatetimeIndex:
    """Tagesindex mit n Tagen."""
    return pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")


def test_rsi_by_hand():
    """Close 10, 11, 12, 11, 13, 12, 14 (Periode 3).

    Δ:        –, 1, 1, −1, 2, −1, 2 → Gewinne 1, 1, 0, 2, 0, 2 / Verluste 0, 0, 1, 0, 1, 0
    Start (Tag 3): Ø Gewinn = 2/3, Ø Verlust = 1/3 → RS 2 → RSI 66.67
    Tag 4: G = (2/3·2 + 2)/3 = 10/9,  V = (1/3·2 + 0)/3 = 2/9   → RS 5    → RSI 83.33
    Tag 5: G = (10/9·2 + 0)/3 = 20/27, V = (2/9·2 + 1)/3 = 13/27 → RS 20/13 → RSI 60.61
    Tag 6: G = (20/27·2 + 2)/3 = 94/81, V = (13/27·2)/3 = 26/81 → RS 47/13 → RSI 78.33
    """
    close = pd.Series([10.0, 11, 12, 11, 13, 12, 14], index=idx(7))
    values = rsi(close, 3)
    assert values.iloc[:3].isna().all()
    expected = [100 - 100 / 3, 100 - 100 / 6, 100 * 20 / 33, 100 * 47 / 60]
    assert values.iloc[3:].tolist() == pytest.approx(expected)


def test_rsi_edge_cases():
    """Nur Gewinne → RSI 100; keine Bewegung → RSI 50 (keine Division durch 0)."""
    assert rsi(pd.Series([1.0, 2, 3, 4, 5], index=idx(5)), 3).iloc[-1] == 100.0
    assert rsi(pd.Series([5.0] * 5, index=idx(5)), 3).iloc[-1] == 50.0


def test_atr_by_hand():
    """ATR nach Wilder (Periode 3).

    Tag  H   L   C     True Range
    0    10  8   9     2  (kein Vortag: H − L)
    1    12  9   11    max(3, |12−9|, |9−9|)   = 3
    2    11  10  10    max(1, |11−11|, |10−11|) = 1
    3    15  12  14    max(3, |15−10|, |12−10|) = 5  (Kurslücke)
    4    14  11  12    max(3, |14−14|, |11−14|) = 3
    5    13  12  12.5  max(1, |13−12|, |12−12|) = 1
    ATR: Tag 2 = (2+3+1)/3 = 2; Tag 3 = (2·2+5)/3 = 3; Tag 4 = (3·2+3)/3 = 3; Tag 5 = (3·2+1)/3 = 7/3
    """
    df = pd.DataFrame({"high": [10.0, 12, 11, 15, 14, 13], "low": [8.0, 9, 10, 12, 11, 12],
                       "close": [9.0, 11, 10, 14, 12, 12.5]}, index=idx(6))
    values = atr(df, 3)
    assert values.iloc[:2].isna().all()
    assert values.iloc[2:].tolist() == pytest.approx([2, 3, 3, 7 / 3])


def test_wilder_smooth_skips_leading_nan():
    """Der Startwert ist der Mittelwert der ersten `period` gültigen Werte."""
    values = wilder_smooth(pd.Series([np.nan, 3.0, 6, 9, 12], index=idx(5)), 3)
    assert values.iloc[:3].isna().all()
    assert values.iloc[3] == 6.0 and values.iloc[4] == pytest.approx((6 * 2 + 12) / 3)


def test_wilder_smooth_too_short():
    """Weniger Werte als die Periode → nur NaN."""
    assert wilder_smooth(pd.Series([1.0, 2.0], index=idx(2)), 3).isna().all()


def test_sma_and_roc_are_causal():
    """SMA und ROC nutzen nur vergangene Werte (erste Werte NaN, keine Zentrierung)."""
    close = pd.Series([1.0, 2, 3, 4, 5], index=idx(5))
    assert sma(close, 3).tolist()[2:] == [2.0, 3.0, 4.0]
    assert roc(close, 2).tolist()[2:] == pytest.approx([2.0, 1.0, 2 / 3])
    assert sma(close, 3).iloc[:2].isna().all() and roc(close, 2).iloc[:2].isna().all()
