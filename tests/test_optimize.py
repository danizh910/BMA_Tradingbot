"""Tests der Optimierung: Grid, Plateau-Check, DSR für die beste Kombination, Heatmaps."""

import copy

import pandas as pd
import pytest

from bot.analysis import optimize
from bot.config import load_strategy_config
from bot.strategies import STRATEGIES, FearGreedTrend, SmaCrossover


@pytest.fixture
def small_grids(monkeypatch):
    """Ersetzt die Grids durch kleine Grids, damit die Tests schnell laufen."""
    cfg = copy.deepcopy(load_strategy_config())
    cfg["s1_sma_crossover"]["param_grid"] = {"fast": [5, 10], "slow": [20, 30]}
    cfg["s4_feargreed_trend"]["param_grid"] = {"greed_level": [55, 60], "fear_level": [25, 30], "ma_slow": [30, 40]}
    monkeypatch.setattr("bot.strategies.base.load_strategy_config", lambda: cfg)
    return cfg


@pytest.mark.parametrize("cls", STRATEGIES)
def test_full_grids_have_100_valid_combinations(cls):
    """Jedes Grid hat laut Auftrag 100 Kombinationen, alle erfüllen die Bedingungen."""
    combos = optimize.param_combinations(cls)
    assert len(combos) == 100
    assert all(cls().constraints({**cls().params, **c}) for c in combos)


def test_constraints_filter_combinations(monkeypatch):
    """Ungültige Kombinationen (fast >= slow) werden nicht getestet."""
    cfg = copy.deepcopy(load_strategy_config())
    cfg["s1_sma_crossover"]["param_grid"] = {"fast": [10, 50, 150], "slow": [100, 200]}
    monkeypatch.setattr("bot.strategies.base.load_strategy_config", lambda: cfg)
    combos = optimize.param_combinations(SmaCrossover)
    assert {(c["fast"], c["slow"]) for c in combos} == {(10, 100), (10, 200), (50, 100), (50, 200), (150, 200)}


def test_plateau_by_hand():
    """Grid a ∈ {1,2,3} × b ∈ {10,20,30}, Sharpe = a + b/10.

    Beste Kombination Mitte (2, 20): Nachbarn (1,20)=3, (3,20)=5, (2,10)=3, (2,30)=5 → Ø 4.
    Ecke (3, 30): Nachbarn (2,30)=5, (3,20)=5 → Ø 5, nur 2 Nachbarn.
    """
    grid = {"a": [1, 2, 3], "b": [10, 20, 30]}
    rows = [{"a": a, "b": b, "sharpe": a + b / 10} for a in grid["a"] for b in grid["b"]]
    results = pd.DataFrame(rows)
    centre = results.index[(results["a"] == 2) & (results["b"] == 20)][0]
    corner = results.index[(results["a"] == 3) & (results["b"] == 30)][0]
    assert optimize.plateau(results, grid, centre) == (pytest.approx(4.0), 4)
    assert optimize.plateau(results, grid, corner) == (pytest.approx(5.0), 2)


def test_grid_search_and_heatmaps(small_grids, random_market, settings, tmp_path):
    """Grid Search liefert eine Zeile pro Kombination mit n_trials; DSR liegt in [0, 1]; PNGs entstehen."""
    for cls, n in ((SmaCrossover, 4), (FearGreedTrend, 8)):
        results = optimize.grid_search(cls, random_market, settings)
        assert len(results) == n and (results["n_trials"] == n).all()
        best = optimize.best_index(results)
        assert results.loc[best, "sharpe"] == results["sharpe"].max()
        dsr = optimize.deflated_sharpe_for_best(results, best, settings["annualization_days"])
        assert 0.0 <= dsr <= 1.0
        path = tmp_path / f"{cls.key}.png"
        optimize.plot_heatmaps(results, cls().param_grid, best, "Test", path)
        assert path.stat().st_size > 0


def test_grid_search_evaluates_only_from_eval_start(small_grids, random_market, settings):
    """Die Kennzahlen beziehen sich nur auf eval_start bis Datenende."""
    results = optimize.grid_search(SmaCrossover, random_market, settings)
    expected_days = len(random_market.loc[settings["eval_start"]:])
    assert (results["n_days"] == expected_days).all()
