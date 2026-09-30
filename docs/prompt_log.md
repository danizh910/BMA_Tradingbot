# Prompt-Log

Ein Eintrag pro Aufgabe. Iterationen = wie oft nachgebessert werden musste (0 = auf Anhieb korrekt).

---

## 2026-09-30 – Projektsetup und Datenpipeline

**Prompt (Zusammenfassung):** Repo `bma-btc-tradingbot` aufsetzen: Struktur, `settings.yaml`, Loader Binance (API + Fallback data.binance.vision), Bitstamp (Aufwärmdaten), Fear & Greed; Rohdaten-Cache mit SHA256; Bereinigung (ffill, nie bfill, Protokoll); Validierungsbericht inkl. Überlappung Bitstamp/Binance; Datensatz mit `source`-Spalte, F&G `shift(1)`, `get_data(split)` mit OOS-Sperre und Protokoll; CLAUDE.md, Doku, Streamlit-Seite «Daten», Tests, README, Git-Init. Noch keine Strategien, kein Backtester.

**Iterationen:** 1. Ein Test deckte einen Fehler in der Ausreisserprüfung auf (ATR nach Datenlücke NaN, siehe KI-Fehlerlog #1). Er wurde von der KI selbst behoben, bevor das Team etwas prüfen musste.

**Geänderte/neue Dateien:**
- `CLAUDE.md`, `README.md`, `pyproject.toml`, `uv.lock`, `.gitignore`, `config/settings.yaml`
- `src/bot/config.py`, `src/bot/data/{raw_cache,loader_binance,loader_bitstamp,loader_feargreed,clean,validate,dataset}.py`
- `src/bot/{strategies,backtest,analysis}/__init__.py` (leer)
- `scripts/fetch_data.py`, `dashboard/app.py`
- `tests/{conftest,test_clean,test_validate,test_dataset,test_loaders}.py`
- `docs/*`, `results/data_validation.md`, `results/cleaning_log.csv`

**Zusätzlich zum Auftrag:** `src/bot/data/raw_cache.py`, damit alle drei Loader denselben Cache und dieselbe Prüfsummenlogik nutzen. Ausserdem die Abschnitte `validation` (ATR-Parameter) und `sources` (URLs) in `settings.yaml`.

**Offene Punkte:** siehe `docs/entscheidungen.md` (Status «offen»), vor allem E3 (flache Kerze), E5 (USD/USDT) und E14 (Aufwärmdaten im OOS-Backtest).
