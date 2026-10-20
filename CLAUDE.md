# CLAUDE.md – Regeln für alle Sessions in diesem Repo

## Projektkontext
Berufsmaturitätsarbeit (BMA) von vier Lernenden. Fragestellung:

> «Inwiefern lässt sich mithilfe von KI-gestützter Softwareentwicklung ein regelbasierter Trading-Bot für Bitcoin realisieren, der im Backtesting (BTC/USDT, Tagesdaten 2018–2025, inkl. Transaktionskosten) auf einem Out-of-Sample-Zeitraum eine höhere risikoadjustierte Performance (Sharpe Ratio, Max Drawdown) als eine Buy-&-Hold-Strategie erzielt, und welchen Einfluss haben Marktphase, Parameterwahl und die Qualität des KI-generierten Codes auf den Erfolg oder Misserfolg?»

Die Qualität des KI-generierten Codes ist selbst Untersuchungsgegenstand. **Nachvollziehbarkeit und Dokumentation sind wichtiger als Eleganz.**

## Daten
- Zugriff auf Kursdaten ausschliesslich über `bot.data.dataset.get_data(split)`.
- Splits: `warmup_is` (inkl. Aufwärmdaten bis is_end), `is`, `oos`, `full`. Grenzen in `config/settings.yaml`.
- Zeilenindex = Tag T (00:00 UTC), `close` = Schlusskurs Tag T (23:59:59 UTC). Spalte `fear_greed` in Zeile T = F&G-Wert vom Tag T−1 (bereits verschoben).
- Neue Daten nur über `scripts/fetch_data.py` laden.

## Harte Regeln
1. **Kein Look-Ahead.** Signale nur mit Daten bis und mit Schlusskurs t. Die Position gilt ab t+1: `position = signal.shift(1)`. Nur kausale Rolling-Fenster (`center=False`). Nie `bfill`.
2. **Keine OOS-Daten ohne ausdrückliche Anweisung** des Teams. `BMA_ALLOW_OOS=1` nie selbst setzen. Jeder OOS-Zugriff wird in `docs/oos_runs.log` protokolliert.
3. **Nur Long oder Cash**, kein Hebel, keine Short-Positionen (Position ∈ [0, 1]).
4. **Gebühren auf jede Positionsänderung:** `kosten = fee × |Δ Position|` (Kauf UND Verkauf).
5. **Keine hart codierten Parameter.** Alles aus `config/settings.yaml` bzw. der Strategie-Config.
6. **Sprache:** Kommentare und Docstrings auf Deutsch, Variablen-/Funktionsnamen auf Englisch.
7. **Jede Funktion hat einen Docstring:** WAS sie tut und WARUM.
8. **Keine externen Backtesting-Libraries** (vectorbt, backtrader, zipline, bt …) für die Kernlogik. pandas/numpy ja.
9. **Keine Systemzeit** (`now()`, `today()`) in der Logik. Ausnahme: Zeitstempel in Protokollen.

## Arbeitsweise
- **Nach jeder Aufgabe** Eintrag in `docs/prompt_log.md`: Datum, Prompt-Zusammenfassung, Anzahl Iterationen (wie oft nachgebessert werden musste), geänderte Dateien, offene Punkte.
- Gefundene Fehler im KI-Code in `docs/ki_fehlerlog.csv` eintragen.
- Bei Unklarheiten **nachfragen**. Getroffene Annahmen in `docs/entscheidungen.md` festhalten.
- Vor Abschluss: `uv run pytest` muss grün sein. Neue Logik bekommt Tests.
- Beim Review `docs/review_checkliste.md` durchgehen.

## Befehle
- Setup: `uv sync`
- Daten: `uv run python scripts/fetch_data.py` (`--refresh` = neu herunterladen)
- Tests: `uv run pytest`
- Optimierung (IS): `uv run python scripts/run_optimization.py`
- In-Sample-Auswertung: `uv run python scripts/run_insample.py`
- OOS (nur mit Freigabe des Teams): `BMA_ALLOW_OOS=1 uv run python scripts/run_oos.py`
- Dashboard: `uv run streamlit run dashboard/app.py`

## Git
- Remote: https://github.com/danizh910/BMA_Tradingbot (`origin`). **Nach jedem Commit sofort pushen** (`git push origin main`, Tags mit `--follow-tags`), damit das ganze Team immer die neuste Version hat.
- Vor dem Push prüfen, dass keine sensiblen Daten dabei sind (Rohdaten in `data/` bleiben ignoriert; keine Tokens, Passwörter, lokalen Pfade).
- Tag `v0.1-ki-unreviewed` = erstes lauffähiges KI-Ergebnis vor dem Review. **Nie verändern oder verschieben.**
- Fehler aus dem Review: Eintrag in `docs/ki_fehlerlog.csv`, Behebung in eigenem Commit mit Message «fix(review): …».

## BMA-Dokumentation (Pflicht in jeder Session)
Grundlage: `docs/vorgaben/bma_vorgaben.md` (Zusammenfassung der Schulvorgaben, im Zweifel gilt das Original).
- Am Ende jeder Session `/session-ende` ausführen bzw. dessen Schritte erledigen.
- Prompts des Teams in `docs/prompt_log.md` und `docs/prompt_sammlung.csv` im Wortlaut festhalten (lange Prompts: Verweis auf `docs/prompts/`). Iterationen ehrlich zählen.
- Jeder gefundene Fehler im KI-Code → `docs/ki_fehlerlog.csv` (auch kleine, auch selbst gefundene; `gefunden_durch` korrekt setzen).
- Neue Quellen nur in `docs/quellen.md` eintragen; nie Quellen, DOIs oder Seitenzahlen erfinden. Unbelegtes als «ungeprüft» markieren (`geprueft = nein`).
- Texte für die Schriftliche Dokumentation: wissenschaftlich, 3. Person, keine «wir»-Form, Gendern ohne Stern/Doppelpunkt. Journal und Einzelreflexion dürfen Ich-/Wir-Form haben.
- Wer etwas gemacht hat, steht in «wer» (aus `git config user.name`). Nicht raten, sondern `[bitte ergänzen]`.
- Keine Schuldokumente (PDF) und keine personenbezogenen Daten ausser Namen der Teammitglieder committen.
- Wichtige Termine aus `docs/vorgaben/bma_vorgaben.md` kennen und bei `/status` darauf hinweisen.
- Befehle: `/session-ende`, `/fehler`, `/quelle`, `/fotostrecke`, `/status`, `/abgabe-auszug`, `/audit` (siehe `.claude/commands/`). Excel-Export: `uv run python scripts/export_prozessunterlagen.py`.
