"""S1 – SMA-Crossover (Trendfolge)."""

import pandas as pd

from bot.strategies.base import Strategy, run_state_machine
from bot.strategies.indicators import sma


class SmaCrossover(Strategy):
    """Long, wenn SMA(fast) > SMA(slow); Cash, wenn SMA(fast) < SMA(slow).

    Bei Gleichheit (SMA(fast) = SMA(slow)) HOLD. Solange SMA(slow) noch nicht
    berechnet werden kann (zu wenig Daten), Cash.
    """

    key = "s1_sma_crossover"
    name = "S1 SMA-Crossover"

    def constraints(self, params: dict) -> bool:
        """Der schnelle Durchschnitt muss kürzer sein als der langsame."""
        return params["fast"] < params["slow"]

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Einstieg bei fast > slow, Ausstieg bei fast < slow (Zustandslogik)."""
        fast = sma(df["close"], self.params["fast"])
        slow = sma(df["close"], self.params["slow"])
        ready = slow.notna() & fast.notna()
        entry = ready & (fast > slow)
        exit_ = ~ready | (fast < slow)
        return run_state_machine(entry, exit_)
