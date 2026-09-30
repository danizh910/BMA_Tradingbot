"""Out-of-Sample-Test: alle Varianten EINMAL auf oos_start bis oos_end.

NUR auf ausdrückliche Anweisung des Teams ausführen:
    BMA_ALLOW_OOS=1 uv run python scripts/run_oos.py

Ablauf:
1. Abbruch ohne BMA_ALLOW_OOS=1 oder bei uncommitteten Änderungen (Arbeitsbereich muss sauber sein).
2. Parameter aus results/optimization/best_params.yaml (In-Sample), keine neue Optimierung.
3. Daten via get_data("full") (Aufwärmdaten + IS für Indikatoren), Auswertung ab oos_start.
4. Resultate mit Commit-Hash nach results/oos/. Der Zugriff wird in docs/oos_runs.log protokolliert.
"""

import os
import subprocess
import sys
from datetime import datetime, timezone

import yaml

from bot.analysis.evaluation import build_variants, evaluate, load_best_params, save_evaluation
from bot.config import RESULTS_DIR, ROOT, load_settings
from bot.data.dataset import OOS_ENV_VAR, get_data

OOS_DIR = RESULTS_DIR / "oos"


def git_output(*args: str) -> str:
    """Führt einen Git-Befehl im Projektordner aus und gibt die Ausgabe zurück."""
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    """Prüft die Voraussetzungen und führt den OOS-Test einmal aus."""
    if os.environ.get(OOS_ENV_VAR) != "1":
        sys.exit(f"Abbruch: OOS-Test nur mit {OOS_ENV_VAR}=1 (ausdrückliche Freigabe des Teams).")
    if git_output("status", "--porcelain"):
        sys.exit("Abbruch: Git-Arbeitsbereich nicht sauber. Zuerst alle Änderungen committen.")
    commit = git_output("rev-parse", "HEAD")

    settings = load_settings()
    df = get_data("full")  # protokolliert den Zugriff in docs/oos_runs.log
    variants = build_variants(load_best_params())
    evaluation = evaluate(df, variants, settings, eval_start=settings["oos_start"], eval_end=settings["oos_end"])
    for table in (evaluation.summary, evaluation.costs):
        table.insert(0, "commit", commit)
    save_evaluation(evaluation, OOS_DIR, "oos",
                    f"Out-of-Sample {settings['oos_start']:%Y-%m-%d} bis {settings['oos_end']:%Y-%m-%d} (Commit {commit[:7]})")

    run_info = {
        "commit": commit,
        # Systemzeit nur für das Protokoll, nicht für die Logik
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "oos_start": str(settings["oos_start"].date()),
        "oos_end": str(settings["oos_end"].date()),
        "best_params": load_best_params(),
    }
    with open(OOS_DIR / "run_info.yaml", "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(run_info, f, allow_unicode=True, sort_keys=False)
    print(evaluation.summary[evaluation.summary["scope"] == "gesamt"].to_string())


if __name__ == "__main__":
    main()
