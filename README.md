# bma-btc-tradingbot

Berufsmaturitätsarbeit (BMA): Ein regelbasierter Bitcoin-Trading-Bot wird mit KI-gestützter Softwareentwicklung gebaut und im Backtesting (BTC/USDT, Tagesdaten 2018–2025, inkl. Transaktionskosten) mit Buy & Hold verglichen. Gemessen wird die risikoadjustierte Performance (Sharpe Ratio, Max Drawdown) im Out-of-Sample-Zeitraum 2023–2025.

**Stand:** Projektstruktur und Datenpipeline. Strategien und Backtester folgen.

## Datenquellen

| Quelle | Zeitraum | Verwendung |
|---|---|---|
| Binance BTC/USDT, 1d (API `/api/v3/klines`, Fallback data.binance.vision) | 2017-08-17 – 2025-12-31 | Hauptdaten |
| Bitstamp BTC/USD, 1d (OHLC-API) | 2016-01-01 – 2017-08-16 | nur Aufwärmdaten für Indikatoren |
| Fear & Greed Index (alternative.me) | ab 2018-02-01 | Stimmungsindikator, um 1 Tag verschoben |

Zeiträume: In-Sample 2018-01-01 – 2022-12-31, Out-of-Sample 2023-01-01 – 2025-12-31 (gesperrt, siehe `CLAUDE.md`).

## Setup

Voraussetzung: Python 3.11+ und [uv](https://docs.astral.sh/uv/) (`pip install uv`).

```bash
uv sync
```

## Daten laden

```bash
uv run python scripts/fetch_data.py            # nutzt gecachte Rohdaten, falls vorhanden
uv run python scripts/fetch_data.py --refresh  # Rohdaten neu herunterladen
```

Ergebnis:
- `data/raw/*.csv`: unveränderte Rohdaten (nicht im Git), Prüfsummen in `docs/data_checksums.txt`
- `data/processed/dataset.csv`: bereinigter, zusammengeführter Datensatz
- `results/data_validation.md`: Validierungsbericht, `results/cleaning_log.csv`: jede Korrektur

Im Code Daten nur so abrufen:

```python
from bot.data.dataset import get_data
df = get_data("is")   # "warmup_is", "is"; "oos"/"full" nur mit BMA_ALLOW_OOS=1
```

## Tests

```bash
uv run pytest        # inkl. Testabdeckung (pytest-cov)
```

## Dashboard

```bash
uv run streamlit run dashboard/app.py
```

## Struktur

```
config/settings.yaml   alle festen Parameter
src/bot/data/          Loader, Bereinigung, Validierung, Datensatz/Splits
src/bot/strategies/    (folgt)
src/bot/backtest/      (folgt)
src/bot/analysis/      (folgt)
scripts/fetch_data.py  Datenpipeline
dashboard/app.py       Streamlit-Dashboard
docs/                  Prompt-Log, KI-Fehlerlog, Review-Checkliste, Entscheidungen, OOS-Protokoll
results/               erzeugte Berichte
```
