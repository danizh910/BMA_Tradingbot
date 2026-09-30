"""Gemeinsame Auswertung aller Varianten (In-Sample und später Out-of-Sample).

WARUM ein gemeinsames Modul: run_insample.py und run_oos.py sollen exakt
denselben Code verwenden. Nur Daten und Auswertungszeitraum unterscheiden sich.
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from bot.analysis.metrics import compute_metrics  # noqa: E402
from bot.analysis.regimes import classify_regimes, regime_metrics  # noqa: E402
from bot.backtest.engine import run_backtest  # noqa: E402
from bot.config import RESULTS_DIR  # noqa: E402
from bot.strategies import STRATEGIES  # noqa: E402
from bot.strategies.base import Strategy  # noqa: E402
from bot.strategies.benchmark import BuyAndHold  # noqa: E402
from bot.strategies.ensemble import Ensemble  # noqa: E402

BEST_PARAMS_FILE = RESULTS_DIR / "optimization" / "best_params.yaml"
BENCHMARK = "Buy & Hold"
SUMMARY_METRICS = ["n_days", "share_days", "total_return", "cagr", "volatility", "sharpe", "sortino",
                   "max_drawdown", "dd_peak", "dd_trough", "dd_recovery", "n_trades", "hit_rate",
                   "avg_exposure", "total_costs"]


@dataclass
class Evaluation:
    """Ergebnisse der Auswertung: Kennzahlen, Kosten-Sensitivität, Equity-Kurven und Trades."""

    summary: pd.DataFrame
    costs: pd.DataFrame
    equity: pd.DataFrame
    trades: pd.DataFrame


def load_best_params(path: Path = BEST_PARAMS_FILE) -> dict:
    """Liest die optimierten Parameter (erzeugt von scripts/run_optimization.py)."""
    if not path.exists():
        raise FileNotFoundError(f"{path} fehlt. Zuerst `uv run python scripts/run_optimization.py` ausführen.")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_variants(best_params: dict) -> dict[str, Strategy]:
    """Erstellt alle Varianten: S1–S4 Standard und optimiert, zwei Ensembles, Buy & Hold."""
    standard = [cls() for cls in STRATEGIES]
    optimized = [cls(best_params[cls.key]["params"]) for cls in STRATEGIES]
    variants = {}
    for std, opt in zip(standard, optimized):
        variants[f"{std.name} (Standard)"] = std
        variants[f"{opt.name} (Optimiert)"] = opt
    variants["Ensemble (Standard)"] = Ensemble(standard, "Ensemble (Standard)")
    variants["Ensemble (Optimiert)"] = Ensemble(optimized, "Ensemble (Optimiert)")
    variants[BENCHMARK] = BuyAndHold()
    return variants


def evaluate(df: pd.DataFrame, variants: dict[str, Strategy], settings: dict,
             eval_start: pd.Timestamp, eval_end: pd.Timestamp | None = None) -> Evaluation:
    """Führt für jede Variante Backtest, Kennzahlen, Marktphasen und Kosten-Sensitivität durch.

    df muss die Aufwärmdaten enthalten (Indikatoren), ausgewertet wird ab eval_start.
    Kosten-Sensitivität: dieselbe Exposure (Parameter NICHT neu optimiert) mit
    fee_per_trade und allen Werten aus cost_sensitivity.
    """
    regimes = classify_regimes(df, settings)
    cost_levels = [settings["fee_per_trade"], *settings["cost_sensitivity"]]
    summary_rows, cost_rows, equity, trades = [], [], {}, []
    for name, strategy in variants.items():
        exposure = strategy.generate_exposure(df)
        for fee in cost_levels:
            result = run_backtest(df, exposure, settings, cost_per_trade=fee, eval_start=eval_start, eval_end=eval_end)
            metrics = compute_metrics(result, settings)
            cost_rows.append({"variant": name, "cost_per_trade": fee,
                              **{k: metrics[k] for k in ["sharpe", "max_drawdown", "cagr", "total_return",
                                                         "total_costs", "n_trades"]}})
            if fee != settings["fee_per_trade"]:
                continue
            summary_rows.append({"variant": name, "scope": "gesamt", "share_days": 1.0,
                                 **{k: metrics[k] for k in SUMMARY_METRICS if k in metrics}})
            for regime, values in regime_metrics(result, regimes, settings).items():
                summary_rows.append({"variant": name, "scope": regime, **values})
            equity[name] = result.daily["equity"]
            trades.append(result.trades.assign(variant=name))
    summary = pd.DataFrame(summary_rows).reindex(columns=["variant", "scope", *SUMMARY_METRICS])
    return Evaluation(summary=summary, costs=pd.DataFrame(cost_rows), equity=pd.DataFrame(equity),
                      trades=pd.concat(trades, ignore_index=True))


def plot_equity(equity: pd.DataFrame, path: Path, title: str) -> None:
    """Equity-Kurven (log-Skala) in zwei Feldern: Standard- und optimierte Varianten, je mit Buy & Hold."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    panels = {"Standard": "Standardparameter", "Optimiert": "Optimierte Parameter"}
    for ax, (tag, panel_title) in zip(axes, panels.items()):
        for name in equity.columns:
            if tag in name:
                ax.plot(equity.index, equity[name], label=name, linewidth=1.3 if "Ensemble" in name else 0.9)
        ax.plot(equity.index, equity[BENCHMARK], label=BENCHMARK, color="black", linewidth=1.6)
        ax.set_yscale("log")
        ax.set_ylabel("Equity (Start = 1, log)")
        ax.set_title(panel_title)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def save_evaluation(evaluation: Evaluation, out_dir: Path, prefix: str, title: str) -> None:
    """Speichert Kennzahlen, Kosten, Equity-Kurven (CSV + PNG) und Trades mit gemeinsamem Präfix."""
    out_dir.mkdir(parents=True, exist_ok=True)
    kw = {"index": False, "lineterminator": "\n"}
    evaluation.summary.to_csv(out_dir / f"{prefix}_summary.csv", **kw)
    evaluation.costs.to_csv(out_dir / f"{prefix}_costs.csv", **kw)
    evaluation.trades.to_csv(out_dir / f"{prefix}_trades.csv", **kw)
    evaluation.equity.to_csv(out_dir / f"{prefix}_equity.csv", lineterminator="\n")
    plot_equity(evaluation.equity, out_dir / f"{prefix}_equity.png", title)
