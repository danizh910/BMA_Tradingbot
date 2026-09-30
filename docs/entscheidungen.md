# Entscheidungen und Annahmen

Jede Annahme mit Datum, Begründung und Status. Status: **offen** = Team soll bestätigen, **bestätigt** = vom Team abgenommen.

## 2026-09-30 – Projektsetup und Datenpipeline

| # | Thema | Entscheidung / Annahme | Begründung | Status |
|---|---|---|---|---|
| E1 | Zeitzone, Tagesdefinition | Alle Zeitstempel in UTC. Zeile T = Binance-Tageskerze mit Eröffnung 00:00 UTC; `close` = Kurs um 23:59:59 UTC von T. | Binance-Tageskerzen sind UTC-basiert; so ist «Tagesschluss T» eindeutig. | offen |
| E2 | F&G-Verschiebung | Der F&G-Wert mit Datum T wird erst für Entscheidungen am Tagesschluss T+1 verwendet (`shift(1)`). Zeile T enthält den Wert von T−1. Der erste nutzbare Wert steht somit am 2018-02-02. | Veröffentlichungszeitpunkt und Datenbasis des Index sind nicht exakt dokumentiert. Konservativ: lieber einen Tag zu spät als Look-Ahead. (Vom Team vorgegeben.) | bestätigt |
| E3 | Fehlende Kurstage | Fehlender Tag: Open = High = Low = Close = letzter bekannter Schlusskurs, Volumen = 0 («flache Kerze»). Nie Backward-Fill. | Ein Forward-Fill jeder Spalte einzeln würde die Spanne (High−Low) des Vortags kopieren und eine Schwankung erfinden. Bei den aktuellen Daten gab es **keine** fehlenden Kurstage, die Regel greift also noch nicht. | offen |
| E4 | Lücken im F&G-Index | Forward-Fill (4 Tage: 2018-04-14 bis 16, 2024-10-26), protokolliert in `results/cleaning_log.csv`. Vor dem 2018-02-01 bleibt F&G leer (NaN). | Forward-Fill ist kausal. Strategien mit F&G müssen NaN vor Februar 2018 selbst behandeln. | offen |
| E5 | Aufwärmdaten USD statt USDT | Bitstamp BTC/USD wird ohne Umrechnung vor Binance BTC/USDT gehängt. | Abweichung in der Überlappung im Mittel 0.8 % (siehe `results/data_validation.md`). Für Indikatoren wie den 200-Tage-Durchschnitt vernachlässigbar. Aufwärmdaten fliessen nie in Renditen ein. | offen |
| E6 | Volumen der Aufwärmdaten | Bitstamp-Volumen (BTC) ist nicht mit Binance-Volumen vergleichbar. | Andere Börse. Volumenbasierte Indikatoren an der Nahtstelle 2017-08-17 sind verzerrt. | offen |
| E7 | Bitstamp-Download bis 2017-12-31 | Rohdaten Bitstamp werden bis zum Tag vor eval_start geladen, im Datensatz aber nur bis 2017-08-16 verwendet. | Nötig für den Überlappungsvergleich 2017-08-17 bis 2017-12-31. | bestätigt |
| E8 | Binance-Zeitraum | Geladen wird binance_start bis oos_end (aus settings.yaml), nicht «bis heute». | Reproduzierbarkeit: ein erneuter Download liefert dieselben Tage; keine Systemzeit in der Logik. | offen |
| E9 | Aufwärmphase Binance | Binance-Daten 2017-08-17 bis 2017-12-31 gehören ebenfalls zur Aufwärmphase (vor eval_start), Spalte `source` = `binance_btcusdt`. | `source` zeigt die Herkunft, nicht die Verwendung. Die Aufwärmphase ergibt sich aus dem Datum (< eval_start). | offen |
| E10 | Datenvalidierung über alle Zeiträume | Validierung und Speicherung umfassen auch den OOS-Zeitraum. Die Sperre greift beim Zugriff über `get_data`. | Datenqualität muss auch für OOS geprüft werden. Der Bericht enthält nur Zählungen und Datumslisten, keine Performance. | offen |
| E11 | Ausreisser-Definition | High − Low > 4 × ATR14. ATR = einfacher Durchschnitt der True Range der **14 Vortage** (ohne den geprüften Tag). Nur Warnung, keine Korrektur. | Der geprüfte Tag soll seine eigene Schwelle nicht erhöhen. Echte Extremtage (z. B. 2020-03-12) sollen nicht gelöscht werden. | offen |
| E12 | Duplikate | Bei doppeltem Datum gilt die erste Zeile. | In den aktuellen Daten keine Duplikate. Die Regel ist nur eine Absicherung. | offen |
| E13 | OOS-Freigabe | Nur exakt `BMA_ALLOW_OOS=1` gibt frei. Protokoll: UTC-Zeitstempel, Split, Git-Commit (+dirty bei uncommitteten Änderungen), aufrufende Datei:Zeile. | Ein OOS-Lauf soll einer exakten Codeversion zugeordnet werden können. | offen |
| E14 | Split «oos» ohne Aufwärmdaten | `get_data("oos")` liefert nur 2023–2025. Für Indikatoren im OOS braucht es die Vorgeschichte, also `get_data("full")` berechnen und danach auf OOS zuschneiden. | Das wird beim Backtester festgelegt. | offen |
| E15 | Dashboard und OOS | Das Dashboard zeigt ohne `BMA_ALLOW_OOS=1` nur Daten bis is_end. | Die OOS-Sperre soll auch visuell gelten. | offen |
| E16 | Bull/Bear im Dashboard | Bull = Schlusskurs > 200-Tage-Durchschnitt (kausal), sonst Bear. Nur Darstellung. | Einfache, verbreitete Definition. Die Marktphasen-Analyse legt ihre Definition später fest. | offen |
| E17 | Rohdaten-Format | Rohdaten werden als CSV mit den Originalfeldern der APIs gespeichert (Werte als Text). Beim F&G ist `time_until_update` enthalten, dadurch ändert sich die Prüfsumme bei jedem `--refresh`. | «Unverändert» speichern. Die Prüfsumme belegt den Stand, der für die Auswertung verwendet wurde. | offen |
