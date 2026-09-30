"""In-Sample-Auswertung aller Varianten (eval_start bis is_end).

Aufruf:  uv run python scripts/run_insample.py   (vorher run_optimization.py)

Varianten: S1–S4 (Standard + optimiert), Ensemble (Standard/Optimiert), Buy & Hold.
Erzeugt in results/:
- insample_summary.csv  Kennzahlen gesamt und pro Marktphase (bull/bear)
- insample_costs.csv    Kosten-Sensitivität (fee_per_trade + cost_sensitivity)
- insample_equity.csv/.png  Equity-Kurven (PNG log-Skala)
- insample_trades.csv   Trades aller Varianten
"""

import pandas as pd

from bot.analysis.evaluation import build_variants, evaluate, load_best_params, save_evaluation
from bot.config import RESULTS_DIR, load_settings
from bot.data.dataset import get_data


def main() -> None:
    """Wertet alle Varianten In-Sample aus und gibt die Gesamtkennzahlen aus."""
    settings = load_settings()
    df = get_data("warmup_is")  # Aufwärmdaten + In-Sample, endet bei is_end
    variants = build_variants(load_best_params())
    evaluation = evaluate(df, variants, settings, eval_start=settings["eval_start"], eval_end=settings["is_end"])
    save_evaluation(evaluation, RESULTS_DIR, "insample",
                    f"In-Sample {settings['eval_start']:%Y-%m-%d} bis {settings['is_end']:%Y-%m-%d}")

    total = evaluation.summary[evaluation.summary["scope"] == "gesamt"].set_index("variant")
    columns = ["sharpe", "sortino", "max_drawdown", "cagr", "total_return", "volatility",
               "n_trades", "hit_rate", "avg_exposure", "total_costs"]
    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.float_format", "{:.3f}".format):
        print(total[columns])
        regimes = evaluation.summary[evaluation.summary["scope"] != "gesamt"]
        print(regimes.pivot(index="variant", columns="scope", values=["sharpe", "max_drawdown", "total_return"]))
        print(evaluation.costs.pivot(index="variant", columns="cost_per_trade", values="sharpe"))


if __name__ == "__main__":
    main()
