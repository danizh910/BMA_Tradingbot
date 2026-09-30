"""Tests für Kennzahlen: von Hand gerechnete Werte und Deflated Sharpe Ratio (Beispiel aus dem Paper)."""

import math

import numpy as np
import pandas as pd
import pytest

from bot.analysis.metrics import (
    cagr, compute_metrics, daily_risk_free, deflated_sharpe_ratio, max_drawdown, sharpe_ratio, sortino_ratio,
)
from bot.backtest.engine import run_backtest
from conftest import price_frame


def series(values: list[float], start: str = "2018-01-01") -> pd.Series:
    """Serie mit Tagesindex ab start (UTC)."""
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D", tz="UTC"), dtype=float)


def ts(day: str) -> pd.Timestamp:
    """Kurzform für einen UTC-Zeitstempel."""
    return pd.Timestamp(day, tz="UTC")


def test_max_drawdown_by_hand():
    """Equity 1.2, 1.5, 1.2, 0.9, 1.35, 1.6: Hoch 1.5 (01-02), Tief 0.9 (01-04) → 0.9/1.5 − 1 = −40 %.

    Erholung am ersten Tag mit Equity >= 1.5: 01-06 (1.6).
    """
    result = max_drawdown(series([1.2, 1.5, 1.2, 0.9, 1.35, 1.6]))
    assert result["max_drawdown"] == pytest.approx(-0.4)
    assert result["dd_peak"] == ts("2018-01-02")
    assert result["dd_trough"] == ts("2018-01-04")
    assert result["dd_recovery"] == ts("2018-01-06")


def test_max_drawdown_counts_start_capital():
    """Verlust am ersten Tag: Hoch ist das Startkapital 1.0 (Vortag), keine Erholung."""
    result = max_drawdown(series([0.8, 0.9]))
    assert result["max_drawdown"] == pytest.approx(-0.2)
    assert result["dd_peak"] == ts("2017-12-31")
    assert pd.isna(result["dd_recovery"])


def test_max_drawdown_zero_when_only_rising():
    """Nur steigende Equity: Drawdown 0, keine Daten."""
    assert max_drawdown(series([1.1, 1.2]))["max_drawdown"] == 0.0


def test_sharpe_by_hand():
    """Renditen 1 %, −2 %, 3 %, 0 %: Mittel 0.5 %, Std (ddof=1) = √(0.0013/3) → SR = 0.005/0.020817 × √365."""
    r = series([0.01, -0.02, 0.03, 0.0])
    expected = 0.005 / math.sqrt(0.0013 / 3) * math.sqrt(365)
    assert sharpe_ratio(r, 0.0, 365) == pytest.approx(expected)


def test_sortino_by_hand():
    """Downside Deviation = √((0 + 0.02² + 0 + 0) / 4) = 0.01 → Sortino = 0.005 / 0.01 × √365."""
    r = series([0.01, -0.02, 0.03, 0.0])
    assert sortino_ratio(r, 0.0, 365) == pytest.approx(0.5 * math.sqrt(365))


def test_division_by_zero_gives_zero():
    """Keine Schwankung bzw. keine Verluste: 0.0 statt inf/NaN."""
    flat = series([0.0, 0.0, 0.0])
    assert sharpe_ratio(flat, 0.0, 365) == 0.0
    assert sortino_ratio(series([0.01, 0.02]), 0.0, 365) == 0.0


def test_risk_free_converted_daily(settings):
    """rf täglich so, dass 365 Tage verzinst genau den Jahreszins ergeben."""
    s = {**settings, "risk_free_rate": 0.05}
    assert (1 + daily_risk_free(s)) ** 365 == pytest.approx(1.05)


def test_cagr_by_hand():
    """Equity 1.21 nach 730 Tagen = 10 % pro Jahr."""
    equity = series([1.0] * 729 + [1.21])
    assert cagr(equity, 365) == pytest.approx(0.10)


def test_compute_metrics_consistent(settings):
    """compute_metrics: Gesamtrendite, Anzahl Trades, Investitionsgrad, Kosten, Trefferquote."""
    df = price_frame([100.0, 100, 110, 121, 100, 100, 90])
    exposure = pd.Series([0.0, 1, 1, 0, 0, 1, 1], index=df.index)
    result = run_backtest(df, exposure, settings, eval_start=ts("2018-01-01"))
    m = compute_metrics(result, settings)
    assert m["total_return"] == pytest.approx(result.daily["equity"].iloc[-1] - 1)
    assert m["n_trades"] == 2
    assert m["hit_rate"] == 0.5  # Trade 1 im Gewinn, Trade 2 im Verlust
    assert m["avg_exposure"] == pytest.approx(3 / 6)
    assert m["total_costs"] == pytest.approx(3 * 0.001)  # Kauf, Verkauf, Kauf
    assert m["n_days"] == 6


def test_hit_rate_nan_without_trades(settings):
    """Ohne Trades ist die Trefferquote nicht definiert (NaN), Sharpe 0."""
    df = price_frame([100.0, 101, 102, 103])
    result = run_backtest(df, pd.Series(0.0, index=df.index), settings, eval_start=ts("2018-01-01"))
    m = compute_metrics(result, settings)
    assert np.isnan(m["hit_rate"]) and m["sharpe"] == 0.0 and m["n_trades"] == 0


def test_deflated_sharpe_paper_example():
    """Zahlenbeispiel aus Bailey & López de Prado (2014), Abschnitt «A numerical example»:

    SR 2.5 (annualisiert), T = 1250 Tage (5 Jahre à 250), N = 100 Versuche,
    V[SR] = 0.5 (annualisiert), Schiefe −3, Kurtosis 10 → DSR ≈ 0.9004.
    Umrechnung in Tageswerte mit 250 Handelstagen (wie im Paper).
    """
    dsr = deflated_sharpe_ratio(sr=2.5 / math.sqrt(250), n_trials=100, sr_variance=0.5 / 250,
                                skew=-3, kurt=10, T=1250)
    assert dsr == pytest.approx(0.9004, abs=5e-4)


def test_deflated_sharpe_decreases_with_more_trials():
    """Mehr Versuche → höhere Hürde SR0 → kleinere DSR. Bei 1 Versuch: keine Selektionskorrektur."""
    kwargs = {"sr": 0.05, "sr_variance": 0.0004, "skew": 0.0, "kurt": 3.0, "T": 1000}
    single, few, many = (deflated_sharpe_ratio(n_trials=n, **kwargs) for n in (1, 10, 1000))
    assert single > few > many
    # n_trials = 1: DSR = Z(SR × √(T−1) / √(1 + SR²/2)) (Probabilistic Sharpe Ratio gegen 0)
    z = 0.05 * math.sqrt(999) / math.sqrt(1 + 0.5 * 0.05**2)
    assert single == pytest.approx(0.5 * (1 + math.erf(z / math.sqrt(2))))
