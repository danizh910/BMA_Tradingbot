---
description: Fehler im KI-Code dokumentieren und beheben – Fehlerlog mit Kennzahlen vorher/nachher, fix(review)-Commit
argument-hint: "<Beschreibung des Fehlers, Datei, wie gefunden>"
---
Gemeldeter Fehler: $ARGUMENTS

1. Fehler nachvollziehen (Code lesen, möglichst mit einem Test, der ihn zeigt). Ist es kein Fehler, das begründen und abbrechen.
2. **Kennzahlen VORHER:** `uv run python scripts/run_insample.py` und Sharpe/Max Drawdown der betroffenen Varianten aus `results/insample_summary.csv` notieren.
3. Neue Zeile in `docs/ki_fehlerlog.csv` (nächste id, Datum, version, datei, kategorie, unterkategorie, beschreibung, gefunden_durch = test | review_team | ki_audit | …, auswirkung, sharpe_vorher, maxdd_vorher).
4. Fehler beheben (Ursache, nicht Symptom), Test ergänzen, `uv run pytest` grün.
5. **Kennzahlen NACHHER:** `run_insample.py` erneut, `sharpe_nachher`, `maxdd_nachher`, `behoben_in_commit` eintragen.
6. Commit «fix(review): <kurz>» (nur Fix + Fehlerlog + Resultate), `git push origin main`. Kurzer Eintrag in `docs/prompt_log.md`.

Tag `v0.1-ki-unreviewed` **nie** verändern, verschieben oder neu setzen. Keine OOS-Daten verwenden.
