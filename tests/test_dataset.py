"""Tests für dataset.py: Zusammenführen, F&G-Verschiebung, Split-Grenzen, OOS-Sperre."""

import pandas as pd
import pytest

from bot.data import dataset
from bot.data.dataset import get_data, merge_sources
from conftest import make_ohlcv


def ts(day: str) -> pd.Timestamp:
    """Kurzform für einen UTC-Zeitstempel."""
    return pd.Timestamp(day, tz="UTC")


# --- Zusammenführen -------------------------------------------------------

def test_merge_sources_warmup_only_before_binance(merged, settings):
    """Bitstamp nur vor binance_start, danach nur Binance; Index lückenlos."""
    warm = merged[merged["source"] == settings["warmup_source"]]
    assert warm.index.min() == settings["warmup_start"]
    assert warm.index.max() == settings["binance_start"] - pd.Timedelta(days=1)
    assert (merged.loc[settings["binance_start"]:, "source"] == "binance_btcusdt").all()
    assert merged.index.is_unique and merged.index.freqstr == "D"
    # Erster Binance-Tag enthält den Binance-Kurs (4000 + Tage seit 2017-08-17 = 4000)
    assert merged.loc[settings["binance_start"], "close"] == 4000.0


def test_merge_sources_rejects_gaps(settings):
    """Eine Lücke in den Eingangsdaten führt zu einem Fehler statt zu stillen Lücken."""
    binance = make_ohlcv("2017-08-17", "2025-12-31").drop(ts("2020-05-05"))
    bitstamp = make_ohlcv("2016-01-01", "2017-12-31")
    with pytest.raises(ValueError):
        merge_sources(bitstamp, binance, pd.Series(dtype=float), settings)


def test_feargreed_shifted_by_one_day(merged):
    """F&G-Wert mit Datum T steht erst in Zeile T+1 (Wert 0 = 2018-02-01)."""
    assert pd.isna(merged.loc[ts("2018-02-01"), "fear_greed"])
    assert merged.loc[ts("2018-02-02"), "fear_greed"] == 0.0
    assert merged.loc[ts("2018-02-03"), "fear_greed"] == 1.0
    assert merged.loc[:ts("2018-01-31"), "fear_greed"].isna().all()


# --- Split-Grenzen --------------------------------------------------------

def test_split_boundaries(merged, settings, monkeypatch, tmp_path):
    """IS und OOS grenzen lückenlos aneinander, ohne Überlappung; full = warmup_is + oos."""
    monkeypatch.setenv("BMA_ALLOW_OOS", "1")
    monkeypatch.setattr(dataset, "OOS_LOG_FILE", tmp_path / "oos.log")
    warmup_is = get_data("warmup_is", merged, settings)
    is_ = get_data("is", merged, settings)
    oos = get_data("oos", merged, settings)
    full = get_data("full", merged, settings)

    assert is_.index.min() == ts("2018-01-01") and is_.index.max() == ts("2022-12-31")
    assert oos.index.min() == ts("2023-01-01") and oos.index.max() == ts("2025-12-31")
    assert is_.index.max() + pd.Timedelta(days=1) == oos.index.min()
    assert is_.index.intersection(oos.index).empty
    assert warmup_is.index.min() == ts("2016-01-01") and warmup_is.index.max() == ts("2022-12-31")
    assert full.index.equals(warmup_is.index.append(oos.index))


def test_unknown_split_raises(merged, settings):
    """Tippfehler im Split-Namen dürfen nicht still einen falschen Zeitraum liefern."""
    with pytest.raises(ValueError):
        get_data("test", merged, settings)


def test_get_data_returns_copy(merged, settings):
    """Änderungen am Ergebnis dürfen den Datensatz nicht verändern."""
    is_ = get_data("is", merged, settings)
    is_["close"] = 0.0
    assert merged.loc[ts("2018-01-01"), "close"] != 0.0


# --- OOS-Sperre -----------------------------------------------------------

@pytest.mark.parametrize("split", ["oos", "full"])
def test_oos_locked_without_env(split, merged, settings, monkeypatch, tmp_path):
    """Ohne BMA_ALLOW_OOS=1 wird der Zugriff verweigert und nichts protokolliert."""
    monkeypatch.delenv("BMA_ALLOW_OOS", raising=False)
    log_file = tmp_path / "oos.log"
    monkeypatch.setattr(dataset, "OOS_LOG_FILE", log_file)
    with pytest.raises(PermissionError):
        get_data(split, merged, settings)
    assert not log_file.exists()


def test_oos_other_values_than_1_stay_locked(merged, settings, monkeypatch):
    """Nur exakt '1' gibt frei (z. B. 'true' oder '0' nicht)."""
    for value in ["0", "true", ""]:
        monkeypatch.setenv("BMA_ALLOW_OOS", value)
        with pytest.raises(PermissionError):
            get_data("oos", merged, settings)


def test_oos_access_is_logged(merged, settings, monkeypatch, tmp_path):
    """Freigegebener Zugriff schreibt Zeitstempel, Split, Commit und Aufrufer ins Log."""
    monkeypatch.setenv("BMA_ALLOW_OOS", "1")
    log_file = tmp_path / "oos.log"
    monkeypatch.setattr(dataset, "OOS_LOG_FILE", log_file)
    get_data("oos", merged, settings)
    line = log_file.read_text(encoding="utf-8").strip()
    assert "split=oos" in line and "commit=" in line
    assert "test_dataset.py" in line and "test_oos_access_is_logged" in line


def test_in_sample_splits_not_logged(merged, settings, monkeypatch, tmp_path):
    """IS-Zugriffe sind frei und erzeugen keinen OOS-Logeintrag."""
    monkeypatch.delenv("BMA_ALLOW_OOS", raising=False)
    log_file = tmp_path / "oos.log"
    monkeypatch.setattr(dataset, "OOS_LOG_FILE", log_file)
    get_data("is", merged, settings)
    get_data("warmup_is", merged, settings)
    assert not log_file.exists()


# --- Speichern/Laden ------------------------------------------------------

def test_save_and_load_roundtrip(merged, monkeypatch, tmp_path):
    """Gespeicherter Datensatz wird identisch (inkl. UTC-Index) wieder eingelesen."""
    monkeypatch.setattr(dataset, "DATASET_FILE", tmp_path / "dataset.csv")
    dataset.save_dataset(merged)
    loaded = dataset.load_dataset()
    pd.testing.assert_frame_equal(loaded, merged, check_freq=False)


def test_load_dataset_missing_file(monkeypatch, tmp_path):
    """Fehlt der Datensatz, gibt es einen klaren Hinweis statt eines Downloads."""
    monkeypatch.setattr(dataset, "DATASET_FILE", tmp_path / "fehlt.csv")
    with pytest.raises(FileNotFoundError):
        dataset.load_dataset()
