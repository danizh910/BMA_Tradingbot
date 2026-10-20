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

---

## 2026-09-30 – Backtester, Strategien, Optimierung, Marktphasen (nur In-Sample)

**Prompt (Zusammenfassung):** Backtester (Exposure 0–1, Position ab t+1, Kosten fee × |Δ Position|, Trades-Liste, Auswertung ab eval_start), Kennzahlen inkl. Deflated Sharpe Ratio, Buy & Hold mit gleicher Startgebühr, vier Strategien mit Zustandslogik (S1 SMA-Crossover, S2 Momentum+ATR, S3 RSI-Reversion, S4 Fear&Greed+MA), gleichgewichtetes Ensemble (Standard/Optimiert), Grid Search nur In-Sample mit Heatmaps, Plateau-Check und DSR, Marktphasen Bull/Bear, In-Sample-Auswertung mit Kosten-Sensitivität, run_oos.py vorbereitet (nicht ausgeführt), Dashboard-Seiten, Tests. Erstes lauffähiges Ergebnis als Tag `v0.1-ki-unreviewed`.

**Iterationen:** 3 (alle vor dem Tag, kein Fehler im Produktivcode durch Tests gefunden)
1. Regeltest für S3 schlug fehl, weil S3 auf den zufälligen Testdaten nie einstieg (Testmarkt fiel von 100 auf 6). Drift erhöht, S3 stieg trotzdem nur 1× ein.
2. Regeltest für S3 mit aktiveren Grid-Parametern (rsi_period 7, oversold 45, overbought 65) → 34 Einstiege. Das Problem lag in den Testdaten, nicht in der Strategie.
3. Titel der Equity-Grafik («Optimiert-Parameter» → «Optimierte Parameter»).
Zusätzlich: Fehler in der eigenen Review-Checkliste aus Schritt 1 (Sortino-Nenner) gefunden und korrigiert, siehe KI-Fehlerlog #2.

**Geänderte/neue Dateien:**
- neu: `config/strategies.yaml`, `src/bot/backtest/engine.py`, `src/bot/analysis/{metrics,optimize,regimes,evaluation}.py`, `src/bot/strategies/{base,indicators,sma_crossover,momentum_atr,rsi_reversion,feargreed_trend,benchmark,ensemble}.py`, `scripts/{run_optimization,run_insample,run_oos}.py`, `tests/{test_engine,test_metrics,test_indicators,test_strategies,test_optimize,test_regimes_evaluation}.py`
- geändert: `src/bot/config.py` (load_strategy_config), `src/bot/strategies/__init__.py`, `dashboard/app.py`, `tests/conftest.py`, `pyproject.toml`/`uv.lock` (matplotlib), `README.md`, `CLAUDE.md`, `docs/entscheidungen.md` (E18–E32, E14/E16 angepasst), `docs/review_checkliste.md`, `docs/ki_fehlerlog.csv`
- Resultate: `results/optimization/*`, `results/insample_*`

**Commit/Tag:** `0414bd0` = `v0.1-ki-unreviewed`

**Offene Punkte:**
- Beste Parameter von S3 und S4 liegen am Rand des Grids (siehe Heatmaps). Das Optimum könnte ausserhalb liegen, das Grid wird aber gemäss Vorgabe nicht erweitert.
- S3 mit Standardparametern handelt nur 2× in 5 Jahren. Die Aussagekraft der Kennzahlen ist entsprechend gering.
- DSR: Welche Versuchszahl gilt (100 pro Strategie oder 400 insgesamt)? Siehe E25.
- Ensemble: tägliche Umschichtung ohne Kosten (E22).
- Alle Annahmen E18–E32 sind noch «offen» und warten auf die Bestätigung durch das Team.

---

## 2026-10-19 – Einführung, Gebrauchsanweisung und Startskript

**Prompt (Zusammenfassung):** Projekteinführung als PowerPoint (fachlich vollständig inkl. Entscheide und aktuellem Stand), genaue Gebrauchsanweisung, ein Skript, das die ganze Pipeline in der richtigen Reihenfolge startet und danach das Dashboard öffnet. Antworten des Teams auf offene Fragen: E19 und E22 bestätigt; E20 Vorschlag «am Ende nochmals 0.1 %», noch zu bestätigen.

**Iterationen:** 2
1. PowerPoint: Kartentext auf der Strategie-Folie überlagerte den Kopf, ein Titel brach um, Beschriftungen im Drawdown-Diagramm überlagerten die Balken. Alles nach der Bildkontrolle behoben.
2. E20 in der Präsentation von «bestätigt» auf «zu bestätigen» korrigiert, weil die Interpretation der Antwort noch nicht bestätigt war.

**Geänderte/neue Dateien:** neu `scripts/run_all.py`, `start.bat`, `docs/anleitung.md`, `docs/BMA_Projekteinfuehrung.pptx`; geändert `README.md`, `docs/entscheidungen.md` (E19/E22 bestätigt, E20 Vorschlag notiert).

**Offene Punkte:** E20 bestätigen und einbauen; DSR 100 vs. 400 Versuche; Grid-Ränder S3/S4; Team-Review.

---

## 2026-10-20 – Metaprompt F: BMA-Dokumentation im Repo verankern

**Prompt:** Wortlaut in `docs/prompts/F_doku.md`. Kein Code in `src/`, `scripts/run_*.py`, bestehenden Tests oder Resultaten geändert.

**Iterationen:** 1. Kommentar zur S1-Heatmap in der Fotostrecke korrigiert (Wertebereich und «kein Plateau» zuerst ungenau abgelesen, nach Bildkontrolle präzisiert).

**Geänderte/neue Dateien:**
- neu: `docs/arbeitsjournal.csv` (4 Einträge aus dem Cowork-Journal unverändert + 4 neue für 30.09., 19.10., 20.10.), `docs/prompt_sammlung.csv` (19 Einträge aus dem Blatt «Prompt-Log», Nr. 17/19 ergänzt, neu Nr. 20–22), `docs/prompts/{A_init,B_umsetzung,C_naiv,D_audit,E_oos}.md` (nur Platzhalter), `docs/prompts/F_doku.md`, `docs/quellen.md`, `docs/fotostrecke.md` + `docs/fotostrecke/*.png` (5 Bilder), `docs/deklaration_entwurf.md`, `docs/status.md`, `docs/import/Arbeitsjournal_BMA_Tradingbot.xlsx`, `.claude/commands/{session-ende,fehler,quelle,fotostrecke,status,abgabe-auszug,audit}.md`, `scripts/export_prozessunterlagen.py`, `tests/test_export_prozessunterlagen.py`
- geändert: `CLAUDE.md` (neuer Abschnitt «BMA-Dokumentation»), `pyproject.toml`/`uv.lock` (openpyxl für den Excel-Export), `docs/Vorgaben/` → `docs/vorgaben/`

**Zusätzlich zum Auftrag:** Q1–Q3 (Sortino & Price 1994, Wilder 1978, Bailey & López de Prado 2014) über Crossref bzw. Open Library geprüft. Die im Journal genannten Deep-Research-Quellen (Q8–Q16) stehen nur mit Kurzangabe drin, ungeprüft.

**Offene Punkte:**
- `docs/import/BMA_Metaprompts_Umsetzung.md` fehlte → Wortlaut A–E nachtragen.
- Git-Name ist `danizh910`, kein Klarname → Spalte «wer» bei den Repo-Einträgen offen.
- `../naiv test/backtest.py` (Naiv-Test, Metaprompt C?) liegt ausserhalb des Repos und ist nirgends dokumentiert.
- Alle `[bitte ergänzen]` in Journal, Prompt-Sammlung, Quellen und Deklaration.
