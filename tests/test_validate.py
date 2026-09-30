"""Tests für validate.py: jede Prüfung muss einen eingebauten Fehler finden."""

import pandas as pd

from bot.data.validate import check_feargreed, check_ohlcv, overlap_stats, write_report
from conftest import make_ohlcv


def ts(day: str) -> pd.Timestamp:
    """Kurzform für einen UTC-Zeitstempel."""
    return pd.Timestamp(day, tz="UTC")


def test_clean_data_has_no_errors(settings):
    """Gültige synthetische Daten dürfen keine Fehler melden."""
    result = check_ohlcv(make_ohlcv("2020-01-01", "2020-03-01"), settings)
    assert all(len(v) == 0 for v in result.values())


def test_each_check_detects_its_error(settings):
    """Jede Prüfung erkennt genau den eingebauten Fehler."""
    df = make_ohlcv("2020-01-01", "2020-03-01")
    df.loc[ts("2020-02-01"), "close"] = -5.0          # Preis <= 0 und Low > min(Open, Close)
    df.loc[ts("2020-02-05"), "high"] = 50.0           # High < max(Open, Close)
    df.loc[ts("2020-02-10"), "volume"] = -1.0         # Volumen < 0
    df.loc[ts("2020-02-20"), "high"] = 10_000.0       # Ausreisser
    df = df.drop(ts("2020-02-15"))                    # fehlender Tag
    df = pd.concat([df, df.loc[[ts("2020-01-10")]]])  # Duplikat

    result = check_ohlcv(df, settings)
    assert list(result["fehlende_tage"]) == [ts("2020-02-15")]
    assert list(result["duplikate"]) == [ts("2020-01-10")]
    assert ts("2020-02-01") in result["preise_<=_0"]
    assert list(result["high_<_max(open,close)"]) == [ts("2020-02-05")]
    assert list(result["low_>_min(open,close)"]) == [ts("2020-02-01")]
    assert list(result["volumen_<_0"]) == [ts("2020-02-10")]
    assert ts("2020-02-20") in result["ausreisser"]


def test_feargreed_gaps():
    """Lücken im F&G-Index werden gefunden."""
    index = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-05"], utc=True)
    result = check_feargreed(pd.Series([1.0, 2.0, 3.0], index=index))
    assert list(result["fehlende_tage"]) == [ts("2020-01-03"), ts("2020-01-04")]


def test_overlap_stats_known_values():
    """Bitstamp 1 % bzw. 3 % über Binance → Mittel 2 %, Maximum 3 % am zweiten Tag."""
    binance = make_ohlcv("2020-01-01", "2020-01-02", close=100.0)
    bitstamp = binance.copy()
    bitstamp["close"] = [101.0, 104.03]
    stats = overlap_stats(bitstamp, binance, ts("2020-01-01"), ts("2020-01-02"))
    assert stats["n_days"] == 2
    assert abs(stats["mean_abs_pct"] - 2.0) < 1e-9
    assert abs(stats["max_abs_pct"] - 3.0) < 1e-9
    assert stats["max_date"] == ts("2020-01-02")


def test_write_report(tmp_path, settings):
    """Der Bericht enthält Abschnitte, Status und Überlappung."""
    df = make_ohlcv("2020-01-01", "2020-01-31")
    stats = overlap_stats(df, df, ts("2020-01-01"), ts("2020-01-31"))
    log = pd.DataFrame([(ts("2020-01-02"), "x", "close", None, 1.0)],
                       columns=["date", "source", "field", "old_value", "new_value"])
    path = tmp_path / "report.md"
    write_report(path, {"Test": (df, check_ohlcv(df, settings))}, stats, log)
    text = path.read_text(encoding="utf-8")
    assert "## Test" in text and "| fehlende_tage | 0 | OK |" in text and "0.000 %" in text
