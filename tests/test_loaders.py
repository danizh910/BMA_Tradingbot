"""Tests für Rohdaten-Cache, Prüfsummen und das Parsen der Loader (ohne Internet)."""

import pandas as pd
import pytest

from bot.config import load_settings
from bot.data import raw_cache
from bot.data.loader_binance import parse_binance
from bot.data.loader_bitstamp import parse_bitstamp
from bot.data.loader_feargreed import parse_feargreed


@pytest.fixture
def cache_dirs(monkeypatch, tmp_path):
    """Leitet Rohdaten und Prüfsummendatei in ein temporäres Verzeichnis um."""
    monkeypatch.setattr(raw_cache, "RAW_DIR", tmp_path)
    monkeypatch.setattr(raw_cache, "CHECKSUM_FILE", tmp_path / "checksums.txt")
    return tmp_path


def test_cache_used_without_refresh(cache_dirs):
    """Ohne refresh wird nicht erneut geladen; Prüfsumme wird geschrieben."""
    calls = []

    def fetch():
        calls.append(1)
        return pd.DataFrame({"a": ["1", "2"]})

    raw_cache.load_raw_csv("x.csv", fetch)
    raw_cache.load_raw_csv("x.csv", fetch)
    assert len(calls) == 1
    assert "x.csv" in (cache_dirs / "checksums.txt").read_text()
    raw_cache.load_raw_csv("x.csv", fetch, refresh=True)
    assert len(calls) == 2


def test_modified_raw_file_detected(cache_dirs):
    """Wurde eine Rohdatei nachträglich verändert, bricht das Laden ab."""
    raw_cache.load_raw_csv("x.csv", lambda: pd.DataFrame({"a": ["1"]}))
    (cache_dirs / "x.csv").write_text("a\n2\n")
    with pytest.raises(ValueError):
        raw_cache.load_raw_csv("x.csv", lambda: pd.DataFrame())


def test_parse_binance_ms_and_us():
    """Millisekunden (API) und Mikrosekunden (data.binance.vision ab 2025) ergeben dasselbe UTC-Datum."""
    raw = pd.DataFrame({
        "open_time": ["1502928000000", "1735689600000000"],
        "open": ["1", "2"], "high": ["1", "2"], "low": ["1", "2"], "close": ["1", "2"], "volume": ["1", "2"],
    })
    df = parse_binance(raw)
    assert list(df.index) == [pd.Timestamp("2017-08-17", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")]
    assert str(df.index.tz) == "UTC"


def test_parse_bitstamp_and_feargreed():
    """Sekunden-Zeitstempel werden zu UTC-Tagen; F&G wird aufsteigend sortiert."""
    bs = parse_bitstamp(pd.DataFrame({"timestamp": ["1451606400"], "open": ["1"], "high": ["1"],
                                      "low": ["1"], "close": ["1"], "volume": ["1"]}))
    assert bs.index[0] == pd.Timestamp("2016-01-01", tz="UTC")
    fg = parse_feargreed(pd.DataFrame({"timestamp": ["1517529600", "1517443200"], "value": ["20", "30"]}))
    assert list(fg) == [30.0, 20.0] and fg.index.is_monotonic_increasing


def test_settings_consistent():
    """settings.yaml: OOS beginnt genau einen Tag nach IS-Ende, Daten sind UTC."""
    s = load_settings()
    assert s["oos_start"] - s["is_end"] == pd.Timedelta(days=1)
    assert str(s["eval_start"].tz) == "UTC"


# --- Download-Logik mit simuliertem Netzwerk ------------------------------

class FakeResponse:
    """Minimaler Ersatz für requests.Response."""

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_binance_pagination(monkeypatch):
    """Die Schleife blättert ab der letzten Kerze weiter, bis eine leere Seite kommt."""
    from bot.data import loader_binance

    day_ms = 86_400_000
    start_ms = 1502928000000
    pages = [[[start_ms + i * day_ms] + ["1"] * 11 for i in range(3)],
             [[start_ms + i * day_ms] + ["1"] * 11 for i in range(3, 5)],
             []]
    seen_starts = []

    def fake_get(url, params, timeout):
        seen_starts.append(params["startTime"])
        return FakeResponse(pages[len(seen_starts) - 1])

    monkeypatch.setattr(loader_binance.requests, "get", fake_get)
    df = loader_binance.fetch_api(load_settings())
    assert len(df) == 5
    assert seen_starts[1] == start_ms + 2 * day_ms + 1


def test_binance_falls_back_to_vision(monkeypatch):
    """Bei Netzwerkfehler der API wird data.binance.vision verwendet."""
    from bot.data import loader_binance

    def failing(settings):
        raise loader_binance.requests.ConnectionError("gesperrt")

    monkeypatch.setattr(loader_binance, "fetch_api", failing)
    monkeypatch.setattr(loader_binance, "fetch_vision", lambda settings: "vision")
    assert loader_binance.fetch(load_settings()) == "vision"


def test_bitstamp_pagination_and_end(monkeypatch):
    """Bitstamp: Seiten werden verknüpft, Tage nach dem Ende verworfen."""
    from bot.data import loader_bitstamp

    s = load_settings()
    end = int((s["eval_start"] - pd.Timedelta(days=1)).timestamp())
    row = lambda t: {"timestamp": str(t), "open": "1", "high": "1", "low": "1", "close": "1", "volume": "1"}
    first = int(s["warmup_start"].timestamp())

    def fake_get(url, params, timeout):
        if params["start"] == first:
            return FakeResponse({"data": {"ohlc": [row(first), row(end - 86400)]}})
        return FakeResponse({"data": {"ohlc": [row(end), row(end + 86400)]}})

    monkeypatch.setattr(loader_bitstamp.requests, "get", fake_get)
    df = loader_bitstamp.fetch(s)
    assert list(df["timestamp"].astype(int)) == [first, end - 86400, end]


def test_bitstamp_error_stops_without_other_source(monkeypatch):
    """Bitstamp-Fehler: Abbruch mit Hinweis, keine Ersatzquelle."""
    from bot.data import loader_bitstamp

    def fake_get(url, params, timeout):
        raise loader_bitstamp.requests.ConnectionError("down")

    monkeypatch.setattr(loader_bitstamp.requests, "get", fake_get)
    with pytest.raises(RuntimeError, match="Team fragen"):
        loader_bitstamp.fetch(load_settings())


def test_feargreed_api_error(monkeypatch):
    """Meldet die F&G-API einen Fehler, wird abgebrochen."""
    from bot.data import loader_feargreed

    monkeypatch.setattr(loader_feargreed.requests, "get",
                        lambda url, timeout: FakeResponse({"data": [], "metadata": {"error": "x"}}))
    with pytest.raises(RuntimeError):
        loader_feargreed.fetch(load_settings())
