"""Tests für den Backtester: Buy & Hold, Grenzfälle, Kosten, Shift, Trades."""

import numpy as np
import pandas as pd
import pytest

from bot.backtest.engine import run_backtest
from conftest import price_frame

EVAL_START = pd.Timestamp("2018-01-01", tz="UTC")


def ts(day: str) -> pd.Timestamp:
    """Kurzform für einen UTC-Zeitstempel."""
    return pd.Timestamp(day, tz="UTC")


def constant(df: pd.DataFrame, value: float) -> pd.Series:
    """Exposure-Serie mit konstantem Wert."""
    return pd.Series(value, index=df.index)


# Kurse: 2017-12-31 = 100 (Aufwärmtag), dann 110, 99, 120, 132
CLOSES = [100.0, 110.0, 99.0, 120.0, 132.0]


def test_buy_and_hold_equals_manual_calculation(settings):
    """Buy & Hold: Kauf zum Schluss 2018-01-01 (110), einmal Gebühr, Wert am Ende bei 132.

    Von Hand (additive Kosten am ersten investierten Tag):
    Tag 01-02: 99/110 − 1 − fee = −0.1 − 0.001 = −0.101
    Tag 01-03: 120/99 − 1 = 0.212121…, Tag 01-04: 132/120 − 1 = 0.1
    Equity = 0.899 × 1.212121… × 1.1 = 1.198666…
    """
    df = price_frame(CLOSES)
    result = run_backtest(df, constant(df, 1.0), settings, eval_start=EVAL_START)
    expected = (1 - 0.1 - 0.001) * (120 / 99) * 1.1
    assert result.daily["equity"].iloc[-1] == pytest.approx(expected, rel=1e-12)
    # Näherung vs. exakte Rechnung (1 − fee) × 132/110: Unterschied nur fee × Rendite
    assert result.daily["equity"].iloc[-1] == pytest.approx((1 - 0.001) * 132 / 110, abs=2e-4)
    assert result.daily["cost"].sum() == pytest.approx(0.001)
    assert list(result.daily["position"]) == [0.0, 1.0, 1.0, 1.0]


def test_exposure_one_equals_buy_and_hold_without_fees(settings):
    """Exposure immer 1 ohne Gebühren = Kursverhältnis Ende / Schluss am eval_start."""
    df = price_frame(CLOSES)
    result = run_backtest(df, constant(df, 1.0), settings, cost_per_trade=0.0, eval_start=EVAL_START)
    assert result.daily["equity"].iloc[-1] == pytest.approx(132 / 110, rel=1e-12)


def test_exposure_zero_has_no_return_and_no_costs(settings):
    """Exposure immer 0: keine Rendite, keine Kosten, keine Trades."""
    df = price_frame(CLOSES)
    result = run_backtest(df, constant(df, 0.0), settings, eval_start=EVAL_START)
    assert (result.daily["net_return"] == 0).all()
    assert result.daily["cost"].sum() == 0
    assert result.daily["equity"].iloc[-1] == 1.0
    assert result.trades.empty


def test_costs_equal_sum_of_position_changes_times_fee(settings):
    """Kosten = Σ |Δ Position| × Fee.

    Exposure (ab eval_start): 1, 0.5, 0.5, 0, 1, 1, 0.25, 0
    Position (shift, Start 0):  0, 1, 0.5, 0.5, 0, 1, 1, 0.25
    |Δ Position|:               0, 1, 0.5, 0,   0.5, 1, 0, 0.75  → Summe 3.75
    """
    df = price_frame([100.0 + i for i in range(9)])
    exposure = pd.Series([0.0, 1, 0.5, 0.5, 0, 1, 1, 0.25, 0], index=df.index)
    result = run_backtest(df, exposure, settings, cost_per_trade=0.002, eval_start=EVAL_START)
    assert list(result.daily["turnover"]) == [0, 1, 0.5, 0, 0.5, 1, 0, 0.75]
    assert result.daily["cost"].sum() == pytest.approx(3.75 * 0.002)


def test_position_is_shifted_by_one_day(settings):
    """«Schummel»-Signal: kennt den Schlusskurs t (steigt heute?) und bringt dank shift(1) keinen Vorteil.

    Kurse abwechselnd 100/110: Nach jedem Anstieg folgt ein Rückgang. Ohne shift(1)
    wäre das Signal an jedem investierten Tag im Gewinn. Mit shift(1) ist es an jedem
    investierten Tag im Verlust.
    """
    df = price_frame([100.0, 110.0] * 10)
    asset_return = df["close"] / df["close"].shift(1) - 1
    cheat = (asset_return > 0).astype(float)
    result = run_backtest(df, cheat, settings, cost_per_trade=0.0, eval_start=EVAL_START)
    invested = result.daily[result.daily["position"] > 0]
    assert len(invested) > 0
    assert (invested["gross_return"] < 0).all()
    assert result.daily["equity"].iloc[-1] < 1


def test_gross_return_uses_previous_exposure(settings):
    """Allgemein: gross_return[t] = exposure[t−1] × Rendite[t] (zufällige Daten)."""
    rng = np.random.default_rng(1)
    df = price_frame(list(100 * np.cumprod(1 + rng.normal(0, 0.03, 60))))
    exposure = pd.Series(rng.choice([0.0, 0.5, 1.0], len(df)), index=df.index)
    daily = run_backtest(df, exposure, settings, cost_per_trade=0.0, eval_start=EVAL_START).daily
    expected = exposure.shift(1).loc[daily.index] * daily["asset_return"]
    expected.iloc[0] = 0.0  # Start in Cash
    pd.testing.assert_series_equal(daily["gross_return"], expected, check_names=False)


def test_trades_list(settings):
    """Trades-Liste: Kauf-/Verkaufstag, Dauer, Rendite inkl. Kosten, offener Trade am Ende.

    Exposure ab 2018-01-01: 1, 1, 0, 0, 1, 1 → Position: 0, 1, 1, 0, 0, 1
    Trade 1: gekauft Schluss 01-01, verkauft Schluss 01-03, 2 Tage investiert
    Trade 2: gekauft Schluss 01-05, am Ende offen, 1 Tag investiert
    """
    df = price_frame([100.0, 100, 110, 121, 100, 100, 90])
    exposure = pd.Series([0.0, 1, 1, 0, 0, 1, 1], index=df.index)
    fee = 0.001
    trades = run_backtest(df, exposure, settings, cost_per_trade=fee, eval_start=EVAL_START).trades
    assert len(trades) == 2
    first, second = trades.iloc[0], trades.iloc[1]
    assert (first["entry_date"], first["exit_date"], first["days_held"]) == (ts("2018-01-01"), ts("2018-01-03"), 2)
    assert first["return"] == pytest.approx((1 + 0.1 - fee) * (1 + 0.1) * (1 - fee) - 1)
    assert not first["is_open"]
    assert (second["entry_date"], second["days_held"], second["is_open"]) == (ts("2018-01-05"), 1, True)
    assert pd.isna(second["exit_date"])
    assert second["return"] == pytest.approx(-0.1 - fee)


@pytest.mark.parametrize("bad", [1.5, -0.5, np.nan])
def test_invalid_exposure_rejected(settings, bad):
    """Hebel (> 1), Short (< 0) und NaN werden abgelehnt."""
    df = price_frame(CLOSES)
    exposure = constant(df, 1.0)
    exposure.iloc[2] = bad
    with pytest.raises(ValueError):
        run_backtest(df, exposure, settings, eval_start=EVAL_START)


def test_exposure_index_must_match(settings):
    """Eine Exposure mit anderem Index wird abgelehnt (sonst stille Verschiebung)."""
    df = price_frame(CLOSES)
    with pytest.raises(ValueError):
        run_backtest(df, constant(df, 1.0).iloc[1:], settings, eval_start=EVAL_START)
