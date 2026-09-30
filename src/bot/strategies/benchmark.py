"""Benchmark Buy & Hold."""

import pandas as pd

from bot.strategies.base import Strategy


class BuyAndHold(Strategy):
    """Immer voll investiert (Exposure 1.0).

    Im Backtester startet jede Variante am eval_start in Cash. Buy & Hold kauft
    deshalb zum Schlusskurs von eval_start und zahlt einmal dieselbe Gebühr
    (fee × |0 → 1|) wie jede Strategie bei einem Einstieg. Kein Verkauf am Ende.
    """

    name = "Buy & Hold"

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Gibt an jedem Tag 1.0 zurück."""
        return pd.Series(1.0, index=df.index, name="exposure")
