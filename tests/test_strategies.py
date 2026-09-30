"""Tests der Strategien: Zustandslogik, Regeln, Kausalität (kein Look-Ahead), F&G-Verzögerung."""

import pandas as pd
import pytest

from bot.backtest.engine import run_backtest
from bot.data.dataset import merge_sources
from bot.strategies import STRATEGIES, FearGreedTrend, MomentumAtr, RsiReversion, SmaCrossover
from bot.strategies.base import Strategy, run_state_machine
from bot.strategies.ensemble import Ensemble
from bot.strategies.indicators import atr, roc, rsi, sma
from conftest import make_ohlcv

CUTS = pd.date_range("2018-01-15", "2022-12-15", freq="37D", tz="UTC")


def ts(day: str) -> pd.Timestamp:
    """Kurzform für einen UTC-Zeitstempel."""
    return pd.Timestamp(day, tz="UTC")


def causality_violations(strategy: Strategy, df: pd.DataFrame) -> list[pd.Timestamp]:
    """Gibt alle Schnittdaten zurück, an denen die Strategie Zukunftsdaten nutzt.

    Idee: Wird die Exposure bis zum Tag «cut» nur mit Daten bis «cut» berechnet,
    muss sie gleich sein wie mit allen Daten. Sonst hat ein Wert ≤ cut Daten > cut gesehen.
    """
    full = strategy.generate_exposure(df)
    return [cut for cut in CUTS if not strategy.generate_exposure(df.loc[:cut]).equals(full.loc[:cut])]


class FutureCheater(Strategy):
    """Absichtlich falsche Strategie: kennt den Schlusskurs von morgen (Close t+1)."""

    name = "Cheater"

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Investiert, wenn der Kurs morgen steigt – nur mit Zukunftsdaten möglich."""
        return (df["close"].shift(-1) > df["close"]).astype(float)


# --- Zustandslogik --------------------------------------------------------

def test_state_machine_hold_logic():
    """Einstieg nur aus Cash, Ausstieg nur investiert, sonst HOLD.

    Tag:    0  1  2  3  4  5
    entry:  F  T  F  F  T  F
    exit:   F  F  F  T  T  F   (Tag 4: in Cash → nur entry zählt)
    Pos.:   0  1  1  0  1  1
    """
    index = pd.date_range("2020-01-01", periods=6, freq="D", tz="UTC")
    entry = pd.Series([False, True, False, False, True, False], index=index)
    exit_ = pd.Series([False, False, False, True, True, False], index=index)
    assert run_state_machine(entry, exit_).tolist() == [0, 1, 1, 0, 1, 1]


# --- Regeln pro Strategie (Übergänge und HOLD) -------------------------------

def rules(strategy: Strategy, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Einstiegs-/Ausstiegsbedingung laut Auftrag, unabhängig vom Strategie-Code formuliert."""
    p, close = strategy.params, df["close"]
    if isinstance(strategy, SmaCrossover):
        fast, slow = sma(close, p["fast"]), sma(close, p["slow"])
        return fast > slow, fast < slow
    if isinstance(strategy, MomentumAtr):
        r, a = roc(close, p["roc_period"]), atr(df, p["atr_period"])
        vol_safe = a < p["atr_mult"] * sma(a, p["atr_baseline"])
        return (r > 0) & vol_safe, (r <= 0) | ~vol_safe
    if isinstance(strategy, RsiReversion):
        value, bull = rsi(close, p["rsi_period"]), close > sma(close, p["trend_ma"])
        return bull & (value < p["oversold"]), (value > p["overbought"]) | ~bull
    fgi, trend_up = df["fear_greed"], sma(close, p["ma_fast"]) > sma(close, p["ma_slow"])
    return (fgi > p["greed_level"]) & trend_up, (fgi < p["fear_level"]) | ~trend_up | fgi.isna()


# Parameter, mit denen die Strategie auf den Testdaten oft handelt. S3 mit Standardwerten
# steigt fast nie ein (RSI < 30 im Aufwärtstrend ist selten), deshalb Grid-Werte mit mehr Trades.
ACTIVE_PARAMS = {RsiReversion: {"rsi_period": 7, "oversold": 45, "overbought": 65}}


@pytest.mark.parametrize("cls", STRATEGIES)
def test_strategy_follows_rules(cls, random_market):
    """Jeder Einstieg erfüllt die Einstiegsregel, jeder Ausstieg die Ausstiegsregel,
    und beim Halten ist die jeweils andere Regel nicht erfüllt (Zeitraum ab eval_start)."""
    strategy = cls(ACTIVE_PARAMS.get(cls))
    df = random_market
    exposure = strategy.generate_exposure(df)
    entry, exit_ = rules(strategy, df)
    prev = exposure.shift(1)
    window = exposure.index >= ts("2018-01-01")
    assert ((exposure == 1) & (prev == 0))[window].any(), "Strategie handelt auf Testdaten nie"
    assert entry[(exposure == 1) & (prev == 0) & window].all()
    assert exit_[(exposure == 0) & (prev == 1) & window].all()
    assert not exit_[(exposure == 1) & (prev == 1) & window].any()
    assert not entry[(exposure == 0) & (prev == 0) & window].any()


# --- Kausalität / Look-Ahead ---------------------------------------------

@pytest.mark.parametrize("cls", STRATEGIES)
def test_strategies_use_no_future_data(cls, random_market):
    """Exposure bis t ist unabhängig davon, ob Daten nach t vorhanden sind."""
    assert causality_violations(cls(), random_market) == []


def test_ensemble_uses_no_future_data(random_market):
    """Auch die Kombination nutzt keine Zukunftsdaten."""
    ensemble = Ensemble([cls() for cls in STRATEGIES], "Ensemble")
    assert causality_violations(ensemble, random_market) == []


def test_future_cheating_signal_is_detected(random_market):
    """Ein Signal, das Close t+1 kennt, wird vom Kausalitätstest erkannt.

    WARUM dieser Test: Der Backtester kann ein solches Signal NICHT erkennen
    (shift(1) schützt nur vor gleichem Tag). Er würde einen perfekten Gewinn
    ausweisen. Deshalb müssen alle Strategien den Kausalitätstest bestehen.
    """
    cheater = FutureCheater()
    assert len(causality_violations(cheater, random_market)) > 0


# --- Parameter ------------------------------------------------------------

def test_unknown_parameter_rejected():
    """Tippfehler im Parameternamen führt zu einem Fehler."""
    with pytest.raises(ValueError):
        SmaCrossover({"slwo": 100})


def test_constraints_enforced():
    """Ungültige Kombinationen (fast >= slow, oversold >= overbought, fear >= greed) werden abgelehnt."""
    with pytest.raises(ValueError):
        SmaCrossover({"fast": 200, "slow": 100})
    with pytest.raises(ValueError):
        RsiReversion({"oversold": 70, "overbought": 65})
    with pytest.raises(ValueError):
        FearGreedTrend({"fear_level": 60, "greed_level": 50})


def test_defaults_from_config():
    """Standardparameter stammen aus config/strategies.yaml."""
    assert SmaCrossover().params == {"fast": 50, "slow": 200}
    assert MomentumAtr().params["atr_mult"] == 1.5


# --- Ensemble -------------------------------------------------------------

def test_ensemble_is_mean_of_members(random_market):
    """Exposure = Mittelwert der vier Einzel-Exposures, Werte nur 0/0.25/0.5/0.75/1."""
    members = [cls() for cls in STRATEGIES]
    exposure = Ensemble(members, "E").generate_exposure(random_market)
    expected = sum(m.generate_exposure(random_market) for m in members) / 4
    pd.testing.assert_series_equal(exposure, expected, check_names=False)
    assert set(exposure.unique()) <= {0.0, 0.25, 0.5, 0.75, 1.0}


# --- Fear & Greed: Verzögerung --------------------------------------------

def test_feargreed_value_affects_position_from_t_plus_2(settings):
    """Ein F&G-Wert mit Datum T beeinflusst die Position frühestens ab T+2.

    Ablauf: F&G-Rohwert T → Zeile T+1 im Datensatz (shift) → Entscheid am Schluss T+1
    → Position ab T+2 (Backtester-shift). Steigende Kurse, damit trend_up erfüllt ist.
    F&G sonst konstant 40 (zwischen fear 30 und greed 50 → kein Einstieg).
    """
    day_t = ts("2019-06-01")
    bitstamp = make_ohlcv("2016-01-01", "2017-12-31", close=400.0)
    binance = make_ohlcv("2017-08-17", "2025-12-31", close=4000.0)
    fg_index = pd.date_range("2018-02-01", "2025-12-31", freq="D", tz="UTC")
    base_fg = pd.Series(40.0, index=fg_index)
    spiked_fg = base_fg.copy()
    spiked_fg[day_t] = 90.0

    positions = []
    for fg in (base_fg, spiked_fg):
        df = merge_sources(bitstamp, binance, fg, settings).loc[:settings["is_end"]]
        result = run_backtest(df, FearGreedTrend().generate_exposure(df), settings)
        positions.append(result.daily["position"])
    base, spiked = positions

    one_day = pd.Timedelta(days=1)
    assert (base == 0).all()
    assert spiked.loc[:day_t + one_day].equals(base.loc[:day_t + one_day])
    assert spiked[day_t + one_day] == 0.0
    assert spiked[day_t + 2 * one_day] == 1.0


def test_feargreed_cash_without_index(random_market):
    """Vor dem ersten F&G-Wert (Februar 2018) ist S4 in Cash."""
    exposure = FearGreedTrend().generate_exposure(random_market)
    assert (exposure[random_market["fear_greed"].isna()] == 0).all()
