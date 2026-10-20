# Quellen (zentrale Sammlung)

Vorgabe Wegleitung 2.3: alle Quellen zentral sammeln, jede KI-gestützte Information mit der 4-Schritte-Methode prüfen.
Neue Quellen nur über `/quelle <DOI|URL|Angabe>` eintragen. **Nie Quellen, DOIs oder Seitenzahlen erfinden.** Unbelegtes bleibt leer bzw. `geprueft = nein`.

`geprueft`: **ja** = Existenz und Metadaten (Titel, Autoren, Jahr) über DOI/Katalog bestätigt · **nein** = noch nicht geprüft · **unsicher** = Prüfung ohne eindeutiges Ergebnis oder Zweifel bekannt.
Ein «ja» heisst noch nicht, dass der Inhalt im Original gelesen wurde – das steht in `gelesen_von`.

## Literatur und Methodik (aus `entscheidungen.md`, `review_checkliste.md`)

| id | APA-7-Angabe | DOI/URL | typ | geprueft | pruefung_4_schritte | autor_vertrauen | kurzinhalt | verwendet_fuer | gelesen_von |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | Sortino, F. A., & Price, L. N. (1994). Performance measurement in a downside risk framework. *The Journal of Investing, 3*(3), 59–64. | https://doi.org/10.3905/joi.3.3.59 | Studie | ja | 2026-10-20: DOI über Crossref aufgelöst, Titel/Autoren/Jahr/Heft stimmen. Inhalt noch nicht im Original geprüft. | Fachzeitschrift (Journal of Investing); Sortino ist Namensgeber der Sortino Ratio. | Misst Performance über das Abwärtsrisiko (Downside Deviation) statt über die gesamte Volatilität. | Kennzahl Sortino (E24, `metrics.py`, Review-Checkliste, KI-Fehlerlog #2); Kap. Methodik | [bitte ergänzen] |
| Q2 | Wilder, J. W. (1978). *New concepts in technical trading systems*. Trend Research. | | Buch | ja | 2026-10-20: Autor, Titel, Jahr, Verlag über Open Library bestätigt. Seitenzahlen für RSI/ATR noch offen. | Originalquelle der Indikatoren RSI und ATR. | Führt RSI, ATR und die Wilder-Glättung ein. | Indikatoren RSI/ATR (E28, `indicators.py`), S2, S3; Kap. Theorie | [bitte ergänzen] |
| Q3 | Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *The Journal of Portfolio Management, 40*(5), 94–107. | https://doi.org/10.3905/jpm.2014.40.5.094 | Studie | ja | 2026-10-20: DOI über Crossref aufgelöst, Titel/Autoren/Jahr/Heft stimmen. In E25 nur als Methode genannt, Autoren aus Crossref. | Fachzeitschrift (Journal of Portfolio Management). | Korrigiert die Sharpe Ratio für die Anzahl getesteter Varianten und nicht normalverteilte Renditen. | Deflated Sharpe Ratio (E25, `optimize.py`); Nebenthese Parameterwahl/Overfitting | [bitte ergänzen] |

## Daten und technische Dokumentation (aus `entscheidungen.md`, URLs aus `config/settings.yaml`)

| id | APA-7-Angabe | DOI/URL | typ | geprueft | pruefung_4_schritte | autor_vertrauen | kurzinhalt | verwendet_fuer | gelesen_von |
|---|---|---|---|---|---|---|---|---|---|
| Q4 | Binance. (o. J.). [bitte ergänzen: Titel der Doku-Seite zum Klines-Endpoint] | https://api.binance.com/api/v3/klines | Doku | nein | | Offizielle API der Börse, von der die Kurse stammen. | Tageskerzen BTC/USDT (OHLCV, UTC). | Datenquelle (E1, E8), Kap. Methodik/Daten | |
| Q5 | Binance. (o. J.). [bitte ergänzen: Titel] | https://data.binance.vision/data/spot/monthly/klines | Doku | nein | | Offizielles Datenarchiv von Binance. | Monatliche Kursarchive als Ersatz, falls die API nicht erreichbar ist. | Datenquelle (Fallback) | |
| Q6 | Bitstamp. (o. J.). [bitte ergänzen: Titel] | https://www.bitstamp.net/api/v2/ohlc/btcusd/ | Doku | nein | | Offizielle API der Börse. | Tageskerzen BTC/USD vor dem Binance-Start (Aufwärmdaten). | Aufwärmdaten (E5, E6, E7) | |
| Q7 | Alternative.me. (o. J.). [bitte ergänzen: Titel] | https://api.alternative.me/fng/?limit=0&format=json | Web | nein | | [bitte ergänzen: Berechnung und Veröffentlichungszeitpunkt sind laut E2 nicht exakt dokumentiert] | Crypto Fear & Greed Index (täglich, ab Februar 2018). | Strategie S4, F&G-Verschiebung (E2, E4) | |

## Aus den Deep-Research-Berichten (im Journal vom 30.09. genannt, noch nicht übernommen)

Nur die im Journal genannte Kurzangabe. Vor einer Verwendung mit `/quelle` prüfen.

| id | APA-7-Angabe | DOI/URL | typ | geprueft | pruefung_4_schritte | autor_vertrauen | kurzinhalt | verwendet_fuer | gelesen_von |
|---|---|---|---|---|---|---|---|---|---|
| Q8 | Gerritsen et al. (2020) | | | nein | | | | | |
| Q9 | Hudson & Urquhart (2021) | | | nein | | | | | |
| Q10 | Detzel et al. (2021) | | | nein | | | | | |
| Q11 | Bailey et al. (2014) | | | nein | | | | | |
| Q12 | Peng et al. (2023) | | | nein | | | | | |
| Q13 | Perry et al. (2023) | | | nein | | | | | |
| Q14 | Cheah (2020) | | | unsicher | Journal 30.09.: wahrscheinlich nicht korrekt belegt. | | | nicht verwenden, bis geprüft | |
| Q15 | Bouteska (2023) | | | unsicher | Journal 30.09.: wahrscheinlich nicht korrekt belegt. | | | nicht verwenden, bis geprüft | |
| Q16 | «Backtrader-Bench» | | | unsicher | Journal 30.09.: wahrscheinlich nicht korrekt belegt. | | | nicht verwenden, bis geprüft | |
