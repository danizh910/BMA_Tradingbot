"""Tests für Marktphasen und die gemeinsame Auswertung (evaluation.py)."""

import pandas as pd
import pytest

from bot.analysis import evaluation
from bot.analysis.regimes import classify_regimes, regime_metrics
from bot.backtest.engine import run_backtest
from bot.strategies import STRATEGIES
from bot.strategies.benchmark import BuyAndHold
from conftest import price_frame


def test_classify_regimes_uses_previous_day(settings):
    """Close 1,2,3,4,5,4,3,2,1 mit SMA(3): Phase von Tag t aus Close(t−1) und SMA(t−1).

    SMA3: –, –, 2, 3, 4, 4.33, 4, 3, 2
    t=3: 3 > 2 bull · t=4: 4 > 3 bull · t=5: 5 > 4 bull · t=6: 4 > 4.33? bear · t=7, t=8 bear
    """
    df = price_frame([1.0, 2, 3, 4, 5, 4, 3, 2, 1])
    regimes = classify_regimes(df, {**settings, "regime_ma_days": 3})
    assert regimes.iloc[:3].isna().all()
    assert regimes.iloc[3:].tolist() == ["bull", "bull", "bull", "bear", "bear", "bear"]


def test_regime_metrics_add_up(settings, random_market):
    """Anteile summieren sich zu 1; verkettete Phasenrenditen ergeben die Gesamtrendite."""
    result = run_backtest(random_market, BuyAndHold().generate_exposure(random_market), settings)
    per_regime = regime_metrics(result, classify_regimes(random_market, settings), settings)
    assert sum(v["share_days"] for v in per_regime.values()) == pytest.approx(1.0)
    growth = (1 + per_regime["bull"]["total_return"]) * (1 + per_regime["bear"]["total_return"])
    assert growth == pytest.approx(result.daily["equity"].iloc[-1])


def test_evaluate_all_variants(settings, random_market, tmp_path):
    """11 Varianten × (gesamt, bull, bear); Kosten-Sensitivität; höhere Gebühr verbessert nie die Sharpe Ratio."""
    defaults = {cls.key: {"params": {k: cls().params[k] for k in cls().param_grid}} for cls in STRATEGIES}
    variants = evaluation.build_variants(defaults)
    assert len(variants) == 11
    result = evaluation.evaluate(random_market, variants, settings, eval_start=settings["eval_start"])

    assert len(result.summary) == 33
    assert len(result.costs) == 11 * (1 + len(settings["cost_sensitivity"]))
    bh = result.summary[(result.summary["variant"] == evaluation.BENCHMARK) & (result.summary["scope"] == "gesamt")]
    assert bh["n_trades"].iloc[0] == 1
    for _, group in result.costs.groupby("variant"):
        assert group.sort_values("cost_per_trade")["sharpe"].is_monotonic_decreasing

    evaluation.save_evaluation(result, tmp_path, "test", "Test")
    for suffix in ("summary.csv", "costs.csv", "trades.csv", "equity.csv", "equity.png"):
        assert (tmp_path / f"test_{suffix}").exists()


def test_missing_best_params(tmp_path):
    """Fehlt best_params.yaml, kommt ein klarer Hinweis."""
    with pytest.raises(FileNotFoundError):
        evaluation.load_best_params(tmp_path / "fehlt.yaml")
