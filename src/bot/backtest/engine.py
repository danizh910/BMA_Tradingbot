"""Backtester: rechnet eine Exposure-Serie (Zielposition) in Renditen, Kosten und Trades um.

Zeitlogik (siehe docs/entscheidungen.md):
- exposure[t] = Zielposition, entschieden mit Daten bis und mit Schlusskurs t.
- Gehandelt wird zum Schlusskurs t. Die Position gilt ab Tag t+1:
  position[t+1] = exposure[t]  (shift(1)).
- Rendite Tag t = position[t] × (Close[t] / Close[t−1] − 1).
- Kosten Tag t = cost_per_trade × |position[t] − position[t−1]|.
- Ausgewertet wird nur ab eval_start. Jede Variante startet dort in Cash
  (position[eval_start] = 0). Der erste Kauf ist also zum Schlusskurs von
  eval_start möglich, genau wie beim Buy & Hold.

WARUM eine eigene Engine: Laut Projektregel keine externen Backtesting-Libraries.
Jede Zeile ist so nachvollziehbar und testbar.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    """Ergebnis eines Backtests.

    daily:  eine Zeile pro Auswertungstag mit exposure, position, asset_return,
            gross_return, turnover, cost, net_return, equity
    trades: eine Zeile pro Trade (siehe extract_trades)
    cost_per_trade: verwendeter Gebührensatz
    """

    daily: pd.DataFrame
    trades: pd.DataFrame
    cost_per_trade: float


def _validate_exposure(df: pd.DataFrame, exposure: pd.Series, settings: dict) -> None:
    """Prüft, dass die Exposure zum Kursindex passt, keine Lücken hat und in [0, 1] liegt.

    WARUM: Ein falscher Index oder NaN würde still zu falschen Renditen führen.
    Werte > 1 wären Hebel, Werte < 0 Short-Positionen – beides laut Projektregel verboten.
    """
    if not exposure.index.equals(df.index):
        raise ValueError("Exposure-Index muss exakt dem Kursindex entsprechen.")
    if exposure.isna().any():
        raise ValueError("Exposure enthält NaN. Strategien müssen fehlende Indikatoren als Cash (0) ausgeben.")
    if (exposure > 1).any():
        raise ValueError("Exposure > 1 (Hebel) ist nicht erlaubt.")
    if settings["long_only"] and (exposure < 0).any():
        raise ValueError("Exposure < 0 (Short) ist nicht erlaubt (long_only).")


def run_backtest(
    df: pd.DataFrame,
    exposure: pd.Series,
    settings: dict,
    cost_per_trade: float | None = None,
    eval_start: pd.Timestamp | None = None,
    eval_end: pd.Timestamp | None = None,
) -> BacktestResult:
    """Führt den Backtest für eine Exposure-Serie durch.

    df:        Kursdaten inkl. Aufwärmdaten (Spalte close), Tagesindex UTC
    exposure:  Zielposition 0.0 (Cash) bis 1.0 (voll investiert) pro Tag, gleicher Index wie df
    cost_per_trade: Gebühr pro Positionsänderung, Standard fee_per_trade aus settings.yaml
    eval_start/eval_end: Auswertungszeitraum, Standard eval_start bis Ende von df

    WARUM Renditen auf dem ganzen df berechnen und erst dann zuschneiden:
    So hat auch der erste Auswertungstag eine korrekte Close-to-Close-Rendite
    (Vortag stammt aus den Aufwärmdaten).
    Netto-Rendite = Brutto-Rendite − Kosten (additive Näherung, siehe entscheidungen.md).
    """
    _validate_exposure(df, exposure, settings)
    fee = settings["fee_per_trade"] if cost_per_trade is None else cost_per_trade
    start = settings["eval_start"] if eval_start is None else eval_start

    close = df["close"]
    asset_return = close / close.shift(1) - 1

    target = exposure.loc[start:eval_end]
    # Position ab t+1; am ersten Auswertungstag Cash (keine Position aus der Aufwärmphase)
    position = target.shift(1).fillna(0.0)
    # Δ Position; für den ersten Tag Differenz zu 0 (Start in Cash)
    turnover = position.diff().fillna(position).abs()
    gross_return = position * asset_return.loc[target.index]
    cost = fee * turnover
    net_return = gross_return - cost

    daily = pd.DataFrame({
        "exposure": target,
        "position": position,
        "asset_return": asset_return.loc[target.index],
        "gross_return": gross_return,
        "turnover": turnover,
        "cost": cost,
        "net_return": net_return,
        "equity": (1 + net_return).cumprod(),
    })
    return BacktestResult(daily=daily, trades=extract_trades(daily), cost_per_trade=fee)


def extract_trades(daily: pd.DataFrame) -> pd.DataFrame:
    """Erstellt die Trades-Liste aus der täglichen Position.

    Definition: Ein Trade ist ein zusammenhängender Abschnitt mit position > 0.
    - entry_date: Tag, zu dessen Schlusskurs gekauft wurde (= erster investierter Tag − 1)
    - exit_date:  Tag, zu dessen Schlusskurs verkauft wurde (= erster Tag in Cash − 1),
                  NaT bei einem am Ende noch offenen Trade
    - days_held:  Anzahl investierter Tage
    - return:     Netto-Rendite über den Abschnitt inkl. Ein- und Ausstiegskosten
                  (der Ausstiegstag mit Rendite 0 und Kosten wird mitgezählt)
    WARUM Schleife: Der Zustand (in einem Trade / nicht in einem Trade) ist so
    direkt lesbar. Teilpositionen (Ensemble 0.25 …) zählen als ein Trade,
    solange die Position > 0 bleibt.
    """
    position = daily["position"].tolist()
    net = daily["net_return"].tolist()
    dates = daily.index
    one_day = pd.Timedelta(days=1)
    rows = []
    start = None
    for i, pos in enumerate(position):
        if start is None and pos > 0:
            start = i
        elif start is not None and pos == 0:
            rows.append(_trade_row(dates, net, start, i, is_open=False, one_day=one_day))
            start = None
    if start is not None:
        rows.append(_trade_row(dates, net, start, len(position) - 1, is_open=True, one_day=one_day))
    return pd.DataFrame(rows, columns=["entry_date", "exit_date", "days_held", "return", "is_open"])


def _trade_row(dates, net: list, start: int, end: int, is_open: bool, one_day: pd.Timedelta) -> dict:
    """Berechnet eine Zeile der Trades-Liste für die Tage start..end (inklusive).

    Bei geschlossenen Trades ist end der erste Tag in Cash (dort fallen die Ausstiegskosten an).
    """
    growth = 1.0
    for r in net[start:end + 1]:
        growth *= 1 + r
    return {
        "entry_date": dates[start] - one_day,
        "exit_date": pd.NaT if is_open else dates[end] - one_day,
        "days_held": end - start + 1 if is_open else end - start,
        "return": growth - 1,
        "is_open": is_open,
    }
