"""S2 – Time-Series-Momentum mit ATR-Volatilitätsfilter."""

import pandas as pd

from bot.strategies.base import Strategy, run_state_machine
from bot.strategies.indicators import atr, roc, sma


class MomentumAtr(Strategy):
    """Investiert bei positivem Momentum, solange die Volatilität nicht erhöht ist.

    ROC = Close_t / Close_(t−roc_period) − 1
    ATR = ATR(atr_period) nach Wilder, ATR_Baseline = SMA(ATR, atr_baseline)
    vol_safe = ATR < atr_mult × ATR_Baseline
    Einstieg: ROC > 0 UND vol_safe · Ausstieg: ROC <= 0 ODER NICHT vol_safe
    """

    key = "s2_momentum_atr"
    name = "S2 Momentum+ATR"

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Berechnet ROC und ATR-Filter und wendet die Zustandslogik an."""
        p = self.params
        momentum = roc(df["close"], p["roc_period"])
        current_atr = atr(df, p["atr_period"])
        baseline = sma(current_atr, p["atr_baseline"])
        ready = momentum.notna() & baseline.notna()
        vol_safe = current_atr < p["atr_mult"] * baseline
        entry = ready & (momentum > 0) & vol_safe
        exit_ = ~ready | (momentum <= 0) | ~vol_safe
        return run_state_machine(entry, exit_)
