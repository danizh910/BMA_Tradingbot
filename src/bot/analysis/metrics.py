"""Kennzahlen für Backtest-Ergebnisse, inkl. Deflated Sharpe Ratio.

Alle Kennzahlen beziehen sich auf tägliche Netto-Renditen r_t im Auswertungszeitraum.
N = annualization_days (365, Krypto handelt täglich).
"""

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from bot.backtest.engine import BacktestResult

EULER_GAMMA = 0.5772156649015329  # Euler-Mascheroni-Konstante (für die DSR)


def daily_risk_free(settings: dict) -> float:
    """Rechnet den jährlichen risikofreien Zins in einen Tageszins um.

    Formel: rf_täglich = (1 + rf_jährlich)^(1/N) − 1.
    WARUM geometrisch: So ergibt der Tageszins über N Tage verzinst genau den Jahreszins.
    """
    return (1 + settings["risk_free_rate"]) ** (1 / settings["annualization_days"]) - 1


def sharpe_ratio(returns: pd.Series, rf_daily: float, periods: int) -> float:
    """Annualisierte Sharpe Ratio.

    Formel: SR = mean(r − rf) / std(r − rf) × √N  (std mit ddof=1).
    Ist die Standardabweichung 0 (z. B. nie investiert), wird 0.0 zurückgegeben
    statt einer Division durch 0 (siehe entscheidungen.md).
    """
    excess = returns - rf_daily
    std = excess.std(ddof=1)
    if not std > 0:  # fängt 0 und NaN ab
        return 0.0
    return float(excess.mean() / std * math.sqrt(periods))


def sortino_ratio(returns: pd.Series, rf_daily: float, periods: int) -> float:
    """Annualisierte Sortino Ratio (nur Abwärtsschwankung im Nenner).

    Formel: Sortino = mean(r − rf) / DD × √N,
    DD (Downside Deviation) = √( (1/T) × Σ min(0, r_t − rf)² ) über ALLE T Tage.
    WARUM über alle Tage: Das ist die Definition nach Sortino & Price (1994).
    Positive Tage zählen mit 0. Die Standardabweichung nur der negativen Tage
    wäre eine andere (verbreitete, aber falsche) Grösse.
    Ohne negative Tage wird 0.0 zurückgegeben (Division durch 0).
    """
    excess = returns - rf_daily
    downside = math.sqrt((excess.clip(upper=0) ** 2).mean())
    if not downside > 0:
        return 0.0
    return float(excess.mean() / downside * math.sqrt(periods))


def max_drawdown(equity: pd.Series) -> dict:
    """Maximaler Drawdown aus der Equity-Kurve mit Datum von Hoch, Tief und Erholung.

    Formel: DD_t = Equity_t / max(Equity_0..t) − 1, MaxDD = min(DD_t).
    Das Startkapital 1.0 (Tag vor dem ersten Auswertungstag) zählt als erstes Hoch,
    damit ein Verlust gleich am ersten Tag erfasst wird.
    peak = Tag des Hochs vor dem Tief, trough = Tag des Tiefs,
    recovery = erster Tag danach mit Equity >= Hoch (NaT, falls nicht erholt).
    """
    start = pd.Series([1.0], index=[equity.index[0] - pd.Timedelta(days=1)])
    curve = pd.concat([start, equity])
    drawdown = curve / curve.cummax() - 1
    value = float(drawdown.min())
    if value == 0:
        return {"max_drawdown": 0.0, "dd_peak": pd.NaT, "dd_trough": pd.NaT, "dd_recovery": pd.NaT}
    trough = drawdown.idxmin()
    peak = curve.loc[:trough].idxmax()
    after = curve.loc[trough:]
    recovered = after[after >= curve.loc[peak]]
    return {
        "max_drawdown": value,
        "dd_peak": peak,
        "dd_trough": trough,
        "dd_recovery": recovered.index[0] if len(recovered) else pd.NaT,
    }


def cagr(equity: pd.Series, periods: int) -> float:
    """Jährliche Wachstumsrate (Compound Annual Growth Rate).

    Formel: CAGR = Equity_Ende^(N / Anzahl Tage) − 1  (Startkapital 1.0).
    """
    end_value = float(equity.iloc[-1])
    if end_value <= 0:
        return -1.0
    return end_value ** (periods / len(equity)) - 1


def compute_metrics(result: BacktestResult, settings: dict) -> dict:
    """Berechnet alle Kennzahlen eines Backtests.

    Rückgabe (Dict):
    - sharpe, sortino, max_drawdown (+ dd_peak/dd_trough/dd_recovery), cagr
    - total_return = Equity_Ende − 1
    - volatility = std(r) × √N (p. a.)
    - n_trades, hit_rate = Anteil Trades mit Rendite > 0 (inkl. offenem Trade; NaN ohne Trades)
    - avg_exposure (Investitionsgrad) = Mittelwert der täglichen Position
    - total_costs = Σ Kosten (als Anteil des Kapitals, additiv)
    - skew, kurtosis (Pearson, Normalverteilung = 3), n_days – für die Deflated Sharpe Ratio
    """
    daily, trades = result.daily, result.trades
    net = daily["net_return"]
    periods = settings["annualization_days"]
    rf = daily_risk_free(settings)
    metrics = {
        "start": daily.index[0],
        "end": daily.index[-1],
        "n_days": len(daily),
        "total_return": float(daily["equity"].iloc[-1] - 1),
        "cagr": cagr(daily["equity"], periods),
        "volatility": float(net.std(ddof=1) * math.sqrt(periods)),
        "sharpe": sharpe_ratio(net, rf, periods),
        "sortino": sortino_ratio(net, rf, periods),
        **max_drawdown(daily["equity"]),
        "n_trades": len(trades),
        "hit_rate": float((trades["return"] > 0).mean()) if len(trades) else np.nan,
        "avg_exposure": float(daily["position"].mean()),
        "total_costs": float(daily["cost"].sum()),
        "skew": float(net.skew()),
        "kurtosis": float(net.kurt() + 3),  # pandas liefert Exzess-Kurtosis
    }
    return metrics


def deflated_sharpe_ratio(sr: float, n_trials: int, sr_variance: float, skew: float, kurt: float, T: int) -> float:
    """Deflated Sharpe Ratio nach Bailey & López de Prado (2014).

    Wahrscheinlichkeit, dass die beste gefundene Sharpe Ratio echt > 0 ist,
    nachdem berücksichtigt wurde, dass n_trials Varianten ausprobiert wurden.

    Alle Grössen in DERSELBEN Frequenz, hier täglich (nicht annualisiert):
    sr = Sharpe Ratio der besten Variante, sr_variance = Varianz der Sharpe Ratios
    aller Versuche, skew = Schiefe, kurt = Kurtosis (Pearson, Normal = 3),
    T = Anzahl Renditebeobachtungen.

    1) Erwartete maximale Sharpe Ratio unter der Nullhypothese (kein echter Vorteil):
       SR0 = √V × ( (1 − γ) × Z⁻¹(1 − 1/N) + γ × Z⁻¹(1 − 1/(N·e)) ),  γ = 0.5772…
    2) DSR = Z( (SR − SR0) × √(T − 1) / √(1 − skew × SR + (kurt − 1)/4 × SR²) )
    Z = Verteilungsfunktion der Standardnormalverteilung, Z⁻¹ deren Inverse.
    Bei n_trials = 1 ist SR0 = 0 (keine Selektion). Ist der Nenner nicht positiv, NaN.
    """
    norm = NormalDist()
    if n_trials > 1:
        sr0 = math.sqrt(sr_variance) * (
            (1 - EULER_GAMMA) * norm.inv_cdf(1 - 1 / n_trials)
            + EULER_GAMMA * norm.inv_cdf(1 - 1 / (n_trials * math.e))
        )
    else:
        sr0 = 0.0
    denominator = 1 - skew * sr + (kurt - 1) / 4 * sr**2
    if not denominator > 0:
        return float("nan")
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(denominator)
    return norm.cdf(z)
