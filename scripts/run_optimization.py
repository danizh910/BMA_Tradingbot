"""Grid Search für S1–S4, NUR In-Sample (eval_start bis is_end, Aufwärmdaten nur für Indikatoren).

Aufruf:  uv run python scripts/run_optimization.py

Erzeugt in results/optimization/:
- <strategie>.csv          alle Kombinationen mit Kennzahlen und n_trials
- <strategie>_heatmap.png  Sharpe-Heatmaps
- best_params.yaml         beste Parameter mit Plateau-Wert und Deflated Sharpe Ratio
"""

import pandas as pd
import yaml

from bot.analysis import optimize
from bot.analysis.evaluation import BEST_PARAMS_FILE
from bot.config import load_settings
from bot.data.dataset import get_data
from bot.strategies import STRATEGIES


def main() -> None:
    """Optimiert jede Strategie, schreibt Resultate und gibt eine Übersicht aus."""
    settings = load_settings()
    df = get_data("warmup_is")  # endet bei is_end, OOS ist nicht enthalten
    out_dir = BEST_PARAMS_FILE.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    periods = settings["annualization_days"]

    all_results = {}
    for cls in STRATEGIES:
        print(f"Optimiere {cls.name} ...")
        all_results[cls] = optimize.grid_search(cls, df, settings)

    # Strengere DSR-Variante: alle Versuche aller Strategien zusammen
    pool = pd.concat([r["sharpe"] for r in all_results.values()], ignore_index=True)

    best_params = {}
    for cls, results in all_results.items():
        results.to_csv(out_dir / f"{cls.key}.csv", index=False, lineterminator="\n")
        best = optimize.best_index(results)
        default = cls()
        is_default = pd.Series(True, index=results.index)
        for name in default.param_grid:
            is_default &= results[name] == default.params[name]
        default_row = results[is_default]
        mean_nb, n_nb = optimize.plateau(results, default.param_grid, best)
        combo = optimize.param_combinations(cls)[best]
        best_params[cls.key] = {
            "name": cls.name,
            "params": combo,
            "sharpe_is": round(float(results.loc[best, "sharpe"]), 4),
            "sharpe_is_default": round(float(default_row["sharpe"].iloc[0]), 4) if len(default_row) else None,
            "plateau_mean_sharpe": round(float(mean_nb), 4),
            "plateau_n_neighbours": n_nb,
            "n_trials": int(len(results)),
            "dsr": round(optimize.deflated_sharpe_for_best(results, best, periods), 4),
            "dsr_all_strategies": round(optimize.deflated_sharpe_for_best(results, best, periods, sharpe_pool=pool), 4),
            "n_trials_all_strategies": int(len(pool)),
        }
        optimize.plot_heatmaps(results, default.param_grid, best,
                               f"{cls.name}: Sharpe Ratio In-Sample {settings['eval_start']:%Y}–{settings['is_end']:%Y}",
                               out_dir / f"{cls.key}_heatmap.png")

    with open(BEST_PARAMS_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Erzeugt von scripts/run_optimization.py (nur In-Sample). Nicht von Hand ändern.\n")
        yaml.safe_dump(best_params, f, allow_unicode=True, sort_keys=False)

    print("\nBeste Parameter (In-Sample):")
    for key, info in best_params.items():
        print(f"  {info['name']}: {info['params']}  Sharpe {info['sharpe_is']:.3f} "
              f"(Standard {info['sharpe_is_default']}), Plateau {info['plateau_mean_sharpe']:.3f} "
              f"({info['plateau_n_neighbours']} Nachbarn), DSR {info['dsr']:.3f} "
              f"(alle Strategien: {info['dsr_all_strategies']:.3f})")


if __name__ == "__main__":
    main()
