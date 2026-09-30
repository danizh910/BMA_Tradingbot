"""Grid Search (nur In-Sample), Plateau-Check, Deflated Sharpe Ratio und Heatmaps.

WARUM nur In-Sample: Wird auf OOS-Daten optimiert, ist der OOS-Test wertlos.
Die Funktionen hier erhalten ausschliesslich Daten aus get_data("warmup_is").
"""

import itertools
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ohne Bildschirm (PNG-Dateien)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from bot.analysis.metrics import compute_metrics, deflated_sharpe_ratio  # noqa: E402
from bot.backtest.engine import run_backtest  # noqa: E402
from bot.strategies.base import Strategy  # noqa: E402

METRIC_COLUMNS = ["sharpe", "sortino", "max_drawdown", "cagr", "total_return", "volatility",
                  "n_trades", "hit_rate", "avg_exposure", "total_costs", "skew", "kurtosis", "n_days"]


def param_combinations(strategy_cls: type[Strategy]) -> list[dict]:
    """Alle gültigen Parameterkombinationen des Grids (kartesisches Produkt, gefiltert mit constraints).

    Feste Parameter (nicht im Grid) behalten ihren Standardwert.
    """
    base = strategy_cls()
    names = list(base.param_grid)
    combos = []
    for values in itertools.product(*(base.param_grid[n] for n in names)):
        params = dict(zip(names, values))
        if base.constraints({**base.params, **params}):
            combos.append(params)
    return combos


def grid_search(strategy_cls: type[Strategy], df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    """Testet alle Kombinationen auf df (Auswertung ab eval_start) und gibt eine Zeile pro Kombination zurück.

    Zielgrösse: Sharpe Ratio (mit fee_per_trade). Spalte n_trials = Anzahl getesteter Kombinationen.
    """
    rows = []
    for params in param_combinations(strategy_cls):
        strategy = strategy_cls(params)
        result = run_backtest(df, strategy.generate_exposure(df), settings)
        metrics = compute_metrics(result, settings)
        rows.append({**params, **{k: metrics[k] for k in METRIC_COLUMNS}})
    results = pd.DataFrame(rows)
    results["n_trials"] = len(results)
    return results


def best_index(results: pd.DataFrame) -> int:
    """Zeilenindex der Kombination mit der höchsten Sharpe Ratio (bei Gleichstand die erste im Grid)."""
    return int(results["sharpe"].idxmax())


def plateau(results: pd.DataFrame, param_grid: dict, best: int) -> tuple[float, int]:
    """Mittlere Sharpe Ratio der direkten Nachbarn der besten Kombination im Grid.

    Direkter Nachbar = genau ein Parameter liegt eine Grid-Stufe höher oder tiefer,
    alle anderen sind gleich (keine Diagonalen). Randpunkte haben weniger Nachbarn.
    WARUM: Liegt die beste Kombination auf einem «Plateau» (Nachbarn ähnlich gut),
    ist sie robuster als eine einzelne Spitze, die eher Zufall (Overfitting) ist.
    Rückgabe: (Mittelwert der Nachbar-Sharpes, Anzahl Nachbarn).
    """
    names = list(param_grid)
    best_row = results.loc[best]
    neighbour_sharpes = []
    for name in names:
        values = param_grid[name]
        i = values.index(best_row[name])
        for j in (i - 1, i + 1):
            if not 0 <= j < len(values):
                continue
            mask = results[name] == values[j]
            for other in names:
                if other != name:
                    mask &= results[other] == best_row[other]
            neighbour_sharpes.extend(results.loc[mask, "sharpe"].tolist())
    if not neighbour_sharpes:
        return float("nan"), 0
    return sum(neighbour_sharpes) / len(neighbour_sharpes), len(neighbour_sharpes)


def deflated_sharpe_for_best(results: pd.DataFrame, best: int, periods: int, n_trials: int | None = None,
                             sharpe_pool: pd.Series | None = None) -> float:
    """Deflated Sharpe Ratio der besten Kombination.

    Die annualisierten Sharpe Ratios werden in Tageswerte umgerechnet (÷ √N),
    weil die DSR-Formel mit der Beobachtungsfrequenz (T Tage) rechnet.
    n_trials/sharpe_pool: Standard = alle Kombinationen dieser Strategie. Für eine
    strengere Variante können alle Versuche aller Strategien übergeben werden.
    """
    pool = results["sharpe"] if sharpe_pool is None else sharpe_pool
    row = results.loc[best]
    daily = math.sqrt(periods)
    return deflated_sharpe_ratio(
        sr=row["sharpe"] / daily,
        n_trials=len(pool) if n_trials is None else n_trials,
        sr_variance=float((pool / daily).var(ddof=1)),
        skew=row["skew"],
        kurt=row["kurtosis"],
        T=int(row["n_days"]),
    )


def plot_heatmaps(results: pd.DataFrame, param_grid: dict, best: int, title: str, path: Path) -> None:
    """Speichert Sharpe-Heatmaps als PNG.

    1. Grid-Parameter = x-Achse, 2. = y-Achse. Bei drei Parametern eine Heatmap
    pro Wert des 3. Parameters. Alle Heatmaps teilen dieselbe Farbskala.
    Die beste Kombination ist mit einem Stern markiert.
    """
    names = list(param_grid)
    x_name, y_name = names[0], names[1]
    facets = param_grid[names[2]] if len(names) > 2 else [None]
    vmin, vmax = results["sharpe"].min(), results["sharpe"].max()
    fig, axes = plt.subplots(1, len(facets), figsize=(5.2 * len(facets), 4.6), squeeze=False)
    best_row = results.loc[best]
    for ax, facet in zip(axes[0], facets):
        subset = results if facet is None else results[results[names[2]] == facet]
        table = subset.pivot(index=y_name, columns=x_name, values="sharpe").reindex(
            index=param_grid[y_name], columns=param_grid[x_name])
        image = ax.imshow(table.to_numpy(), origin="lower", cmap="viridis", vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(table.columns)), [str(v) for v in table.columns], rotation=45)
        ax.set_yticks(range(len(table.index)), [str(v) for v in table.index])
        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        for yi, y in enumerate(table.index):
            for xi, x in enumerate(table.columns):
                value = table.loc[y, x]
                if pd.notna(value):
                    ax.text(xi, yi, f"{value:.2f}", ha="center", va="center", fontsize=7, color="white")
        if facet is None or best_row[names[2]] == facet:
            ax.plot(param_grid[x_name].index(best_row[x_name]), param_grid[y_name].index(best_row[y_name]),
                    marker="*", markersize=18, color="red", markeredgecolor="white")
        ax.set_title(f"{names[2]} = {facet}" if facet is not None else "")
    fig.colorbar(image, ax=axes[0].tolist(), label="Sharpe Ratio (In-Sample)")
    fig.suptitle(title)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
