"""Gleichgewichtete Kombination mehrerer Strategien."""

import pandas as pd

from bot.strategies.base import Strategy


class Ensemble(Strategy):
    """Exposure = Mittelwert der Einzel-Exposures (bei vier Strategien: 0, 0.25, 0.5, 0.75 oder 1).

    WARUM keine optimierten Gewichte: Gleichgewichtung braucht keine weiteren
    Parameter und kann deshalb nicht zusätzlich auf In-Sample überangepasst werden.
    """

    def __init__(self, members: list[Strategy], name: str):
        """members: bereits parametrisierte Einzelstrategien; name: Anzeigename."""
        self.members = members
        self.name = name
        self.params = {m.key: m.params for m in members}
        self.param_grid = {}

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Mittelwert der Exposures aller Mitglieder pro Tag."""
        exposures = pd.concat([m.generate_exposure(df) for m in self.members], axis=1)
        return exposures.mean(axis=1).rename("exposure")
