"""Tests für clean.py: Forward-Fill, Volumen 0, kein Backward-Fill, Protokoll."""

import numpy as np
import pandas as pd

from bot.data.clean import clean_feargreed, clean_ohlcv
from conftest import make_ohlcv


def test_missing_day_filled_with_previous_close_and_zero_volume():
    """Ein fehlender Tag erhält den Schlusskurs des Vortags (nicht des Folgetags) und Volumen 0."""
    df = make_ohlcv("2020-01-01", "2020-01-05").drop(pd.Timestamp("2020-01-03", tz="UTC"))
    cleaned, log = clean_ohlcv(df, "test")

    day = pd.Timestamp("2020-01-03", tz="UTC")
    assert len(cleaned) == 5
    assert (cleaned.loc[day, ["open", "high", "low", "close"]] == 101.0).all()  # Vortag-Close
    assert cleaned.loc[day, "volume"] == 0.0
    assert len(log) == 5  # 4 Preisfelder + Volumen
    assert set(log["field"]) == {"open", "high", "low", "close", "volume"}


def test_no_backward_fill_at_start():
    """Fehlende Werte am Anfang dürfen nicht mit späteren Werten gefüllt werden."""
    df = make_ohlcv("2020-01-01", "2020-01-04")
    df.iloc[0, df.columns.get_loc("close")] = np.nan
    cleaned, _ = clean_ohlcv(df, "test")
    assert np.isnan(cleaned["close"].iloc[0])


def test_consecutive_missing_days_use_last_known_close():
    """Mehrere fehlende Tage hintereinander übernehmen alle den letzten bekannten Schlusskurs."""
    df = make_ohlcv("2020-01-01", "2020-01-06")
    df = df.drop(pd.to_datetime(["2020-01-03", "2020-01-04"], utc=True))
    cleaned, _ = clean_ohlcv(df, "test")
    assert list(cleaned["close"]) == [100.0, 101.0, 101.0, 101.0, 104.0, 105.0]


def test_duplicates_removed_and_logged():
    """Doppelte Tage: erste Zeile bleibt, Duplikat wird protokolliert entfernt."""
    df = make_ohlcv("2020-01-01", "2020-01-03")
    df = pd.concat([df, df.iloc[[1]].assign(close=999.0)])
    cleaned, log = clean_ohlcv(df, "test")
    assert len(cleaned) == 3
    assert cleaned["close"].iloc[1] == 101.0
    assert list(log["old_value"]) == ["duplikat"]


def test_feargreed_forward_fill_only():
    """F&G-Lücken werden vorwärts gefüllt und protokolliert."""
    index = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-04"], utc=True)
    filled, log = clean_feargreed(pd.Series([10.0, 20.0, 40.0], index=index))
    assert list(filled) == [10.0, 20.0, 20.0, 40.0]
    assert len(log) == 1
