# Gebrauchsanweisung bma-btc-tradingbot

Für alle im Team. Was du wann ausführst, wo du Resultate findest und was du nie tun darfst.

---

## 1. Einmalig einrichten

1. Python 3.11 oder neuer installieren (python.org, beim Installieren «Add to PATH» anhaken).
2. In einer Konsole: `pip install uv`
3. Repo klonen bzw. Ordner `bma-btc-tradingbot` öffnen.

Fertig. Alle Pakete installiert `start.bat` automatisch.

---

## 2. Normaler Gebrauch: ein Doppelklick

**`start.bat` im Projektordner doppelklicken.** Das Skript macht alles in der richtigen Reihenfolge:

| Schritt | Was passiert | Dauer |
|---|---|---|
| 0 | Pakete installieren/aktualisieren (`uv sync`) | beim ersten Mal 1–2 min, danach Sekunden |
| 1 | Daten laden und prüfen (aus dem Cache, kein Download) | 1 s |
| 2 | 91 automatische Tests | ca. 30 s |
| 3 | Optimierung: je 100 Parameterkombinationen pro Strategie (nur 2018–2022) | ca. 10 s |
| 4 | Auswertung aller 11 Varianten gegen Buy & Hold (nur 2018–2022) | ca. 2 s |
| 5 | Dashboard öffnet sich im Browser | – |

- Bricht ein Schritt ab, stoppt alles mit «ABBRUCH in Schritt X». Die Fehlermeldung steht direkt darüber.
- Dashboard beenden: im schwarzen Fenster `Ctrl + C`, dann Fenster schliessen.
- Ohne Doppelklick, in einer Konsole im Projektordner: `python -m uv run python scripts/run_all.py`
  - Optionen: `--refresh` lädt die Rohdaten neu herunter, `--no-dashboard` startet am Ende kein Dashboard.

### Wann was ausführen?

| Situation | Was tun |
|---|---|
| Projekt anschauen / präsentieren | `start.bat` |
| Code wurde geändert (z. B. nach einem Review-Fix) | `start.bat`. Die Tests müssen grün sein, die Resultate werden neu berechnet |
| Nur das Dashboard öffnen (Resultate existieren schon) | `python -m uv run streamlit run dashboard/app.py` |
| Nur die Tests | `python -m uv run pytest` |
| Daten neu herunterladen (selten! ändert die Datenbasis) | `python -m uv run python scripts/run_all.py --refresh`, danach die Prüfsummen in `docs/data_checksums.txt` committen |
| Parameter oder Grid ändern | `config/strategies.yaml` bearbeiten, dann `start.bat`. Die Änderung in `docs/entscheidungen.md` begründen |

---

## 3. Wo finde ich was?

### Resultate (werden von `start.bat` erzeugt)

| Datei | Inhalt |
|---|---|
| Dashboard → «Daten» | Kursverlauf, 200-Tage-Linie, Bull/Bear, Fear & Greed |
| Dashboard → «Strategien» | Kennzahlen-Tabelle, Equity-Kurven, Kosten-Sensitivität, Trades |
| Dashboard → «Optimierung» | Heatmaps, Standard vs. optimiert, Plateau, DSR |
| Dashboard → «Marktphasen» | Sharpe/Drawdown pro Bull- und Bear-Phase |
| Dashboard → «KI-Fehlerlog» | gefundene Fehler im KI-Code |
| `results/insample_summary.csv` | alle Kennzahlen (öffnet sich in Excel) |
| `results/insample_equity.png` | Equity-Kurven als Bild |
| `results/optimization/*_heatmap.png` | Heatmaps pro Strategie |
| `results/optimization/best_params.yaml` | beste Parameter + Plateau + DSR |
| `results/data_validation.md` | Datenqualitätsbericht |

### Tests

- Das Testergebnis steht im schwarzen Fenster bei Schritt 2: `91 passed` = alles grün.
- **Testabdeckung im Browser:** `htmlcov/index.html` doppelklicken. Dort siehst du pro Datei, welche Codezeilen von Tests ausgeführt werden (grün) und welche nicht (rot).
- Die Tests selbst stehen in `tests/`. Jeder Test hat einen deutschen Docstring, oft mit Handrechnung, z. B. RSI und ATR in `tests/test_indicators.py`, Max Drawdown in `tests/test_metrics.py`.

### Definitionen

| Was | Wo |
|---|---|
| Zeiträume, Gebühr, 365 Tage, risikofreier Zins | `config/settings.yaml` |
| Standardparameter und Grids der Strategien | `config/strategies.yaml` |
| Alle Annahmen mit Begründung (E1–E32) | `docs/entscheidungen.md` |
| Regeln für die KI | `CLAUDE.md` |
| Review-Prüfpunkte | `docs/review_checkliste.md` |
| Backtester | `src/bot/backtest/engine.py` |
| Strategien | `src/bot/strategies/` (eine Datei pro Strategie) |
| Kennzahlen-Formeln | `src/bot/analysis/metrics.py` |

---

## 4. Review-Ablauf (Code der KI prüfen)

1. `docs/review_checkliste.md` Punkt für Punkt durchgehen.
2. Fehler gefunden?
   - Eintrag in `docs/ki_fehlerlog.csv`: Kategorie, wie gefunden, Sharpe/Drawdown vorher.
   - Fehler beheben (selbst oder mit Claude), dann `start.bat`, Sharpe/Drawdown nachher eintragen.
   - Commit mit Message `fix(review): <kurze Beschreibung>`.
3. **Der Tag `v0.1-ki-unreviewed` wird nie verändert.** Er ist der Vergleichsstand «KI-Code ohne Review».

---

## 5. Out-of-Sample-Test (2023–2025): nur EINMAL, nur mit Freigabe

**Erst ausführen, wenn:** das Review abgeschlossen ist, alle Entscheide in `docs/entscheidungen.md` bestätigt sind und das Team gemeinsam «jetzt» sagt.

1. Alles committen (`git status` muss leer sein, sonst bricht das Skript ab).
2. In PowerShell im Projektordner:
   ```powershell
   $env:BMA_ALLOW_OOS="1"; python -m uv run python scripts/run_oos.py
   ```
3. Resultate in `results/oos/` committen.

Danach werden **keine Parameter mehr geändert**. Sonst ist der OOS-Test wertlos, weil ihr die Strategie unbewusst an die Testdaten anpasst. Jeder OOS-Zugriff steht mit Zeit und Commit in `docs/oos_runs.log`.

---

## 6. Nie tun

- `BMA_ALLOW_OOS=1` setzen, «nur um kurz zu schauen».
- Parameter ändern, nachdem OOS gelaufen ist.
- Dateien in `data/raw/` von Hand ändern (die Prüfsumme erkennt das).
- Den Tag `v0.1-ki-unreviewed` löschen oder verschieben.
