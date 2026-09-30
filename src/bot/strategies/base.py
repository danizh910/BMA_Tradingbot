"""Basisklasse für alle Strategien und die gemeinsame Zustandslogik (Einstieg/Ausstieg/HOLD).

WARUM eine Basisklasse: Backtester, Optimierung und Auswertung behandeln
alle Strategien gleich (params, param_grid, constraints, generate_exposure).
"""

import pandas as pd

from bot.config import load_strategy_config


class Strategy:
    """Gemeinsame Schnittstelle aller Strategien.

    key:        Schlüssel in config/strategies.yaml ("" = Strategie ohne Parameter)
    name:       Anzeigename
    params:     aktuelle Parameter (Standardwerte aus der Config, überschreibbar)
    param_grid: Werte für die Grid Search (aus der Config)
    """

    key: str = ""
    name: str = ""

    def __init__(self, params: dict | None = None, config: dict | None = None):
        """Lädt Standardparameter und Grid aus der Config und überschreibt sie mit `params`.

        WARUM Prüfung unbekannter Parameter: Ein Tippfehler (z. B. «slwo») würde
        sonst still den Standardwert verwenden.
        """
        cfg = {"params": {}, "param_grid": {}}
        if self.key:
            cfg = (config or load_strategy_config())[self.key]
        unknown = set(params or {}) - set(cfg["params"])
        if unknown:
            raise ValueError(f"{self.name}: unbekannte Parameter {sorted(unknown)}")
        self.params = {**cfg["params"], **(params or {})}
        self.param_grid = cfg["param_grid"]
        if not self.constraints(self.params):
            raise ValueError(f"{self.name}: Parameter verletzen die Bedingungen: {self.params}")

    def constraints(self, params: dict) -> bool:
        """Gibt True zurück, wenn die Parameterkombination gültig ist (Standard: immer)."""
        return True

    def generate_exposure(self, df: pd.DataFrame) -> pd.Series:
        """Gibt pro Tag die Zielposition (0.0 bis 1.0) zurück, entschieden am Schlusskurs t.

        Muss nur Daten bis und mit t verwenden. Der Backtester verschiebt um einen Tag.
        """
        raise NotImplementedError


def run_state_machine(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    """Zustandslogik: aus Einstiegs- und Ausstiegsbedingungen wird die Position.

    Regeln pro Tag t (Zustand = in Cash oder investiert):
    - in Cash und entry[t]      → investiert (1.0)
    - investiert und exit_[t]   → Cash (0.0)
    - sonst HOLD                → Zustand bleibt
    WARUM Schleife: Der Zustand hängt vom Vortag ab (HOLD), das ist als Schleife
    direkt lesbar. Im Cash wird nur entry geprüft, investiert nur exit_.
    Sind beide gleichzeitig wahr, entscheidet also der aktuelle Zustand.
    """
    in_market = False
    out = []
    for enter_now, exit_now in zip(entry.tolist(), exit_.tolist()):
        if not in_market and enter_now:
            in_market = True
        elif in_market and exit_now:
            in_market = False
        out.append(1.0 if in_market else 0.0)
    return pd.Series(out, index=entry.index, name="exposure")
