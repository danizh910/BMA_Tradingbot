# Review-Checkliste

Bei jedem Review von KI-generiertem Code durchgehen. Gefundene Fehler → `docs/ki_fehlerlog.csv`.

## Zeit und Look-Ahead
- [ ] **Signal-Shift:** Position = `signal.shift(1)`. Das Signal von Tag t wirkt erst ab t+1.
- [ ] **Ausführungszeitpunkt:** Handel zum Schlusskurs t (bzw. Eröffnung t+1), klar definiert und überall gleich.
- [ ] **UTC:** Alle Zeitstempel tz-aware in UTC, keine naiven Datumswerte, keine lokale Zeitzone.
- [ ] **F&G-Verschiebung:** Spalte `fear_greed` ist bereits um 1 Tag verschoben und wird nicht nochmals oder gar nicht verschoben verwendet.
- [ ] **Kein bfill:** kein `bfill`, `fillna(method="bfill")` oder `backfill`.
- [ ] **Keine zentrierten Fenster:** `rolling(..., center=False)`, kein `shift(-n)` für Features.
- [ ] **Keine Systemzeit:** kein `now()`/`today()` in der Logik (nur in Protokollen).
- [ ] **Aufwärmphase:** Indikatoren werden auf Daten inkl. Aufwärmdaten berechnet, Renditen/Kennzahlen erst ab eval_start (bzw. oos_start).

## Daten
- [ ] **Lückenloser Datumsindex:** Tagesfrequenz, keine Lücken, keine Duplikate (`asfreq("D")`).
- [ ] **IS-Isolation der Optimierung:** Parameter nur auf In-Sample optimiert, kein OOS-Zugriff (`docs/oos_runs.log` prüfen).

## Kosten und Ausführung
- [ ] **Gebühren bei Kauf UND Verkauf:** `fee × |Δ Position|` bei jeder Änderung.
- [ ] **Slippage:** berücksichtigt oder bewusst weggelassen und in `entscheidungen.md` begründet.
- [ ] **Buy & Hold mit gleicher Startgebühr:** Benchmark zahlt die Einstiegsgebühr ebenfalls.
- [ ] **Cash-Rendite 0:** in Cash-Phasen Tagesrendite 0 (keine Zinsen).
- [ ] **Nur Long/Cash:** Position ∈ [0, 1], kein Hebel.

## Kennzahlen
- [ ] **√365:** Annualisierung mit `annualization_days` = 365 (Krypto), nicht 252.
- [ ] **rf täglich:** risikofreier Zins in Tageszins umgerechnet, bevor er abgezogen wird.
- [ ] **Drawdown aus Equity-Kurve:** Max Drawdown = min(Equity / laufendes Maximum − 1), nicht aus Einzelrenditen.
- [ ] **Sortino nur Downside:** Nenner = Standardabweichung nur der negativen Renditen.
- [ ] **Division durch 0:** z. B. Standardabweichung 0 (keine Trades) → definiertes Ergebnis statt inf/NaN-Absturz.

## Allgemein
- [ ] Keine hart codierten Parameter (alles aus `settings.yaml`/Strategie-Config).
- [ ] Jede Funktion mit Docstring (WAS und WARUM), deutsch.
- [ ] Tests vorhanden und grün (`uv run pytest`).
