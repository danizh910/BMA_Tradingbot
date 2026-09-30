"""Gemeinsame Test-Hilfen: synthetische Daten statt echter Downloads.

WARUM: Tests sollen ohne Internet laufen und bekannte, von Hand
nachrechenbare Werte verwenden.
"""

import pandas as pd
import pytest

from bot.config import load_settings


def make_ohlcv(start: str, end: str, close: float = 100.0) -> pd.DataFrame:
    """Erzeugt lückenlose, gültige Tageskerzen mit steigendem Schlusskurs (close, close+1, ...)."""
    index = pd.date_range(start, end, freq="D", tz="UTC", name="date")
    c = pd.Series(range(len(index)), index=index, dtype=float) + close
    return pd.DataFrame({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 10.0})


@pytest.fixture
def settings() -> dict:
    """Echte Projekteinstellungen (Split-Grenzen sollen genau diese sein)."""
    return load_settings()


@pytest.fixture
def merged(settings) -> pd.DataFrame:
    """Zusammengeführter synthetischer Datensatz über den gesamten Projektzeitraum."""
    from bot.data.dataset import merge_sources

    bitstamp = make_ohlcv("2016-01-01", "2017-12-31", close=400.0)
    binance = make_ohlcv("2017-08-17", "2025-12-31", close=4000.0)
    fg_index = pd.date_range("2018-02-01", "2025-12-31", freq="D", tz="UTC")
    fear_greed = pd.Series(range(len(fg_index)), index=fg_index, dtype=float)
    return merge_sources(bitstamp, binance, fear_greed, settings)
