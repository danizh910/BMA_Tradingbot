# bma-btc-tradingbot

Berufsmaturitätsarbeit (BMA): Ein regelbasierter Bitcoin-Trading-Bot wird mit KI-gestützter Softwareentwicklung gebaut und im Backtesting (BTC/USDT, Tagesdaten 2018–2025, inkl. Transaktionskosten) mit Buy & Hold verglichen. Gemessen wird die risikoadjustierte Performance (Sharpe Ratio, Max Drawdown) im Out-of-Sample-Zeitraum 2023–2025.

**Stand:** Datenpipeline, Backtester, vier Strategien, Ensemble, Optimierung und In-Sample-Auswertung. Der Out-of-Sample-Test ist vorbereitet, aber noch nicht ausgeführt.

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

## Backtests (nur In-Sample)

```bash
uv run python scripts/run_optimization.py   # Grid Search S1–S4 → results/optimization/
uv run python scripts/run_insample.py       # alle Varianten vs. Buy & Hold → results/insample_*
```

Strategie-Parameter und Grids: `config/strategies.yaml`.

Out-of-Sample (nur auf ausdrückliche Freigabe des Teams, sauberer Git-Stand nötig):

```bash
BMA_ALLOW_OOS=1 uv run python scripts/run_oos.py   # → results/oos/
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
config/strategies.yaml Strategie-Parameter und Optimierungs-Grids
src/bot/strategies/    S1–S4, Buy & Hold, Ensemble, Indikatoren
src/bot/backtest/      Backtester (engine.py)
src/bot/analysis/      Kennzahlen, Optimierung, Marktphasen, Auswertung
scripts/               fetch_data, run_optimization, run_insample, run_oos
dashboard/app.py       Streamlit-Dashboard
docs/                  Prompt-Log, KI-Fehlerlog, Review-Checkliste, Entscheidungen, OOS-Protokoll
results/               erzeugte Berichte
```
