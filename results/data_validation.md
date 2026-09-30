# Datenvalidierung

Automatisch erzeugt durch `scripts/fetch_data.py`. Prüfung auf Rohdaten vor der Bereinigung.

## Binance BTC/USDT (Hauptdaten)

Zeitraum: 2017-08-17 bis 2025-12-31, 3059 Zeilen (roh)

| Prüfung | Anzahl | Status | Tage |
|---|---:|---|---|
| fehlende_tage | 0 | OK |  |
| duplikate | 0 | OK |  |
| preise_<=_0 | 0 | OK |  |
| high_<_max(open,close) | 0 | OK |  |
| low_>_min(open,close) | 0 | OK |  |
| volumen_<_0 | 0 | OK |  |
| ausreisser | 26 | WARNUNG | 2017-11-29, 2018-10-15, 2018-11-14, 2018-11-19, 2019-02-08, 2019-02-24, 2019-04-02, 2019-04-03, 2019-05-11, 2019-06-27, 2019-09-24, 2019-10-25, 2019-10-26, 2020-03-12, 2020-07-27 … (+11) |

## Bitstamp BTC/USD (Aufwärmdaten)

Zeitraum: 2016-01-01 bis 2017-12-31, 731 Zeilen (roh)

| Prüfung | Anzahl | Status | Tage |
|---|---:|---|---|
| fehlende_tage | 0 | OK |  |
| duplikate | 0 | OK |  |
| preise_<=_0 | 0 | OK |  |
| high_<_max(open,close) | 0 | OK |  |
| low_>_min(open,close) | 0 | OK |  |
| volumen_<_0 | 0 | OK |  |
| ausreisser | 9 | WARNUNG | 2016-01-15, 2016-05-28, 2016-05-29, 2016-08-02, 2016-10-11, 2017-01-05, 2017-02-09, 2017-03-10, 2017-11-29 |

## Fear & Greed Index

Zeitraum: 2018-02-01 bis 2026-09-30, 3160 Zeilen (roh)

| Prüfung | Anzahl | Status | Tage |
|---|---:|---|---|
| fehlende_tage | 4 | FEHLER | 2018-04-14, 2018-04-15, 2018-04-16, 2024-10-26 |
| duplikate | 0 | OK |  |

## Überlappung Bitstamp (BTC/USD) vs. Binance (BTC/USDT)

Zeitraum 2017-08-17 bis 2017-12-31, 137 gemeinsame Tage. Relative Abweichung der Schlusskurse = Bitstamp / Binance − 1.

| Kennzahl | Wert |
|---|---:|
| mittlere absolute Abweichung | 0.805 % |
| mittlere Abweichung (mit Vorzeichen) | +0.430 % |
| maximale absolute Abweichung | 9.917 % (am 2017-12-23) |

## Bereinigung (clean.py)

Anzahl Korrekturen: 4. Details: `results/cleaning_log.csv`.

| Quelle | Feld | Korrekturen |
|---|---|---:|
| feargreed | fear_greed | 4 |
