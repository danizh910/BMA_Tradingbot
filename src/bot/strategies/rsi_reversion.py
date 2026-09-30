"""S3 – RSI Mean Reversion mit 200-Tage-Trendfilter."""

import pandas as pd

from bot.strategies.base import Strategy, run_state_machine
from bot.strategies.indicators import rsi, sma


class RsiReversion(Strategy):
    """Kauft Rücksetzer (RSI überverkauft), aber nur im Aufwärtstrend.

    bull = Close > SMA(trend_ma)
    Einstieg: bull UND RSI < oversold · Ausstieg: RSI > overbought ODER NICHT bull
    """

    key = "s3_rsi_reversion"
    name = "S3 RSI-Reversion"

    def constraints(self, params: dict) -> bool:
        """Die Überverkauft-Schwelle muss unter der Überkauft-Schwelle liegen."""
        return params["oversold"] < params["overbought"]

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Berechnet RSI und Trendfilter und wendet die Zustandslogik an."""
        p = self.params
        rsi_values = rsi(df["close"], p["rsi_period"])
        trend = sma(df["close"], p["trend_ma"])
        ready = rsi_values.notna() & trend.notna()
        bull = df["close"] > trend
        entry = ready & bull & (rsi_values < p["oversold"])
        exit_ = ~ready | (rsi_values > p["overbought"]) | ~bull
        return run_state_machine(entry, exit_)
