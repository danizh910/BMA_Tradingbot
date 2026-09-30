"""S4 – Fear & Greed Index kombiniert mit einem Trendfilter (Sentiment)."""

import pandas as pd

from bot.strategies.base import Strategy, run_state_machine
from bot.strategies.indicators import sma


class FearGreedTrend(Strategy):
    """Investiert bei Gier-Stimmung im Aufwärtstrend, steigt bei Angst oder Trendbruch aus.

    FGI = Spalte fear_greed (in Zeile t steht bereits der Wert vom Vortag, siehe dataset.py)
    trend_up = SMA(Close, ma_fast) > SMA(Close, ma_slow)
    Einstieg: FGI > greed_level UND trend_up · Ausstieg: FGI < fear_level ODER NICHT trend_up
    Ohne F&G-Wert (vor Februar 2018): Cash.
    """

    key = "s4_feargreed_trend"
    name = "S4 Fear&Greed+MA"

    def constraints(self, params: dict) -> bool:
        """Angst-Schwelle unter Gier-Schwelle, schneller SMA kürzer als langsamer."""
        return params["fear_level"] < params["greed_level"] and params["ma_fast"] < params["ma_slow"]

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Wendet die Zustandslogik auf F&G-Schwellen und Trendfilter an.

        WARUM kein erneuter shift: fear_greed ist im Datensatz bereits um einen
        Tag verschoben. Ein zweiter shift würde den Wert unnötig verzögern.
        """
        p = self.params
        fgi = df["fear_greed"]
        fast = sma(df["close"], p["ma_fast"])
        slow = sma(df["close"], p["ma_slow"])
        ready = fgi.notna() & slow.notna() & fast.notna()
        trend_up = fast > slow
        entry = ready & (fgi > p["greed_level"]) & trend_up
        exit_ = ~ready | (fgi < p["fear_level"]) | ~trend_up
        return run_state_machine(entry, exit_)
