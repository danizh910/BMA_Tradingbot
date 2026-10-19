"""Führt die ganze In-Sample-Pipeline in der richtigen Reihenfolge aus und startet danach das Dashboard.

Aufruf:  uv run python scripts/run_all.py [--refresh] [--no-dashboard]
         (oder Doppelklick auf start.bat im Projektordner)

Reihenfolge:
1. fetch_data.py        Daten laden (Cache), prüfen, bereinigen
2. pytest               alle Tests; Abdeckungsbericht in htmlcov/index.html
3. run_optimization.py  Grid Search S1–S4 (nur In-Sample)
4. run_insample.py      alle Varianten vs. Buy & Hold (nur In-Sample)
5. Streamlit-Dashboard  öffnet sich im Browser

Der Out-of-Sample-Test (run_oos.py) wird hier bewusst NIE gestartet:
Er braucht die ausdrückliche Freigabe des Teams (siehe docs/anleitung.md).
WARUM ein Skript: Die Reihenfolge ist wichtig (Optimierung vor Auswertung),
und bricht ein Schritt ab, sollen die folgenden nicht mit alten Resultaten weiterlaufen.
"""

import argparse
import subprocess
import sys
import time

from bot.config import ROOT


def run_step(number: int, title: str, args: list[str]) -> None:
    """Startet einen Schritt als eigenen Prozess und bricht die Pipeline bei einem Fehler ab."""
    print(f"\n{'=' * 70}\n[{number}/5] {title}\n{'=' * 70}", flush=True)
    start = time.perf_counter()
    result = subprocess.run([sys.executable, *args], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"\nABBRUCH in Schritt {number} ({title}). Fehlermeldung oben lesen; "
                 "die folgenden Schritte wurden nicht ausgeführt.")
    print(f"--> Schritt {number} OK ({time.perf_counter() - start:.0f} s)")


def main() -> None:
    """Liest die Optionen und führt die Schritte nacheinander aus."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="Rohdaten neu herunterladen")
    parser.add_argument("--no-dashboard", action="store_true", help="Dashboard am Ende nicht starten")
    args = parser.parse_args()

    run_step(1, "Daten laden und prüfen", ["scripts/fetch_data.py", *(["--refresh"] if args.refresh else [])])
    run_step(2, "Tests", ["-m", "pytest", "-q", "--cov-report=term", "--cov-report=html"])
    run_step(3, "Optimierung (In-Sample)", ["scripts/run_optimization.py"])
    run_step(4, "In-Sample-Auswertung", ["scripts/run_insample.py"])

    print("\nFertig. Resultate: results/  ·  Testabdeckung: htmlcov/index.html  ·  Datenbericht: results/data_validation.md")
    if args.no_dashboard:
        return
    print(f"\n{'=' * 70}\n[5/5] Dashboard startet im Browser (beenden: Ctrl+C in diesem Fenster)\n{'=' * 70}", flush=True)
    subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"], cwd=ROOT)


if __name__ == "__main__":
    main()
