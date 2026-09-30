"""Gemeinsame Test-Hilfen: synthetische Daten statt echter Downloads.

WARUM: Tests sollen ohne Internet laufen und bekannte, von Hand
nachrechenbare Werte verwenden.
"""

import numpy as np
import pandas as pd
import pytest

from bot.config import load_settings


def price_frame(closes: list[float], start: str = "2017-12-31") -> pd.DataFrame:
    """Kleiner Kurs-DataFrame (nur close + OHLC gleich close) für Backtester-Tests."""
    index = pd.date_range(start, periods=len(closes), freq="D", tz="UTC", name="date")
    c = pd.Series(closes, index=index, dtype=float)
    return pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1.0})


@pytest.fixture
def random_market() -> pd.DataFrame:
    """Zufälliger, aber reproduzierbarer Markt 2016–2022 (Seed 42) mit OHLC und F&G.

    WARUM: Auf zufälligen Kursen lösen alle Strategien Signale aus. Damit
    lassen sich Kausalität (kein Look-Ahead) und Wertebereiche prüfen.
    """
    rng = np.random.default_rng(42)
    index = pd.date_range("2016-01-01", "2022-12-31", freq="D", tz="UTC", name="date")
    close = 100 * np.exp(np.cumsum(rng.normal(0.0015, 0.04, len(index))))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.01, len(index))))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.01, len(index))))
    fear_greed = pd.Series(rng.integers(0, 101, len(index)).astype(float), index=index)
    fear_greed[fear_greed.index < pd.Timestamp("2018-02-02", tz="UTC")] = np.nan
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": 1.0,
                         "source": "test", "fear_greed": fear_greed}, index=index)


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
