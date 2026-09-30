"""Lädt BTC/USDT-Tageskerzen von Binance (öffentlicher Klines-Endpoint, Fallback data.binance.vision).

WARUM: Binance ist die Hauptdatenquelle für Auswertung und Backtest
(ab binance_start). Rohdaten werden unverändert gespeichert; die Umwandlung
in Zahlen und UTC-Zeitstempel passiert erst in parse_binance().
"""

import io
import zipfile

import pandas as pd
import requests

from bot.data.raw_cache import load_raw_csv

RAW_FILE = "binance_btcusdt_1d.csv"
# Spaltennamen gemäss Binance-API-Dokumentation (Reihenfolge der Kline-Felder)
COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]
PAGE_LIMIT = 1000  # technisches Maximum der API pro Aufruf, kein Modellparameter
TIMEOUT_S = 30


def _to_ms(ts: pd.Timestamp) -> int:
    """Wandelt einen Zeitstempel in Millisekunden seit 1970 (Format der Binance-API)."""
    return int(ts.timestamp() * 1000)


def _period_ms(settings: dict) -> tuple[int, int]:
    """Gibt Start und Ende (inkl. letztem Tag bis 23:59:59.999) in ms zurück.

    WARUM: Das Ende kommt aus settings.yaml und nicht aus der Systemzeit,
    damit ein erneutes Laden dieselbe Datenmenge liefert.
    """
    start = _to_ms(settings["binance_start"])
    end = _to_ms(settings["oos_end"] + pd.Timedelta(days=1)) - 1
    return start, end


def fetch_api(settings: dict) -> pd.DataFrame:
    """Lädt alle Tageskerzen paginiert (max. 1000 pro Aufruf) über /api/v3/klines.

    WARUM: Die API liefert höchstens 1000 Kerzen pro Anfrage; darum wird ab der
    letzten erhaltenen Kerze weitergeblättert, bis das Ende erreicht ist.
    """
    start, end = _period_ms(settings)
    rows = []
    while start <= end:
        params = {
            "symbol": settings["symbol"], "interval": settings["interval"],
            "startTime": start, "endTime": end, "limit": PAGE_LIMIT,
        }
        resp = requests.get(settings["sources"]["binance_api"], params=params, timeout=TIMEOUT_S)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        start = batch[-1][0] + 1  # nächste Seite beginnt nach der letzten Kerze
    return pd.DataFrame(rows, columns=COLUMNS)


def fetch_vision(settings: dict) -> pd.DataFrame:
    """Fallback: lädt Monats-ZIP-Dateien von data.binance.vision.

    WARUM: Falls die API (z. B. regional) gesperrt ist, bietet Binance dieselben
    Kerzen als statische Dateien an. Achtung: Ab 2025 sind die Zeitstempel dort
    in Mikrosekunden; das wird in parse_binance() behandelt.
    """
    start, end = _period_ms(settings)
    symbol, interval = settings["symbol"], settings["interval"]
    months = pd.period_range(settings["binance_start"].tz_localize(None), settings["oos_end"].tz_localize(None), freq="M")
    frames = []
    for month in months:
        url = f"{settings['sources']['binance_vision']}/{symbol}/{interval}/{symbol}-{interval}-{month}.zip"
        resp = requests.get(url, timeout=TIMEOUT_S)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            frame = pd.read_csv(zf.open(zf.namelist()[0]), header=None, names=COLUMNS, dtype=str)
        frames.append(frame[frame["open_time"].str.isdigit()])  # evtl. Kopfzeile entfernen
    df = pd.concat(frames, ignore_index=True)
    open_ms = _open_time_ms(df["open_time"])
    return df[(open_ms >= start) & (open_ms <= end)].reset_index(drop=True)


def fetch(settings: dict) -> pd.DataFrame:
    """Versucht zuerst die API, bei Netzwerk-/HTTP-Fehler den Fallback data.binance.vision."""
    try:
        return fetch_api(settings)
    except requests.RequestException as err:
        print(f"WARNUNG: Binance-API fehlgeschlagen ({err}), verwende data.binance.vision")
        return fetch_vision(settings)


def load_binance(settings: dict, refresh: bool = False) -> pd.DataFrame:
    """Gibt die Binance-Rohdaten zurück (aus dem Cache oder frisch geladen)."""
    return load_raw_csv(RAW_FILE, lambda: fetch(settings), refresh)


def _open_time_ms(open_time: pd.Series) -> pd.Series:
    """Normalisiert Zeitstempel auf Millisekunden.

    WARUM: data.binance.vision liefert ab 2025 Mikrosekunden. Werte > 1e14 können
    keine Millisekunden sein (das wäre nach dem Jahr 5000) und werden durch 1000 geteilt.
    """
    t = open_time.astype("int64")
    return t.where(t < 10**14, t // 1000)


def parse_binance(raw: pd.DataFrame) -> pd.DataFrame:
    """Wandelt Rohdaten in einen OHLCV-DataFrame mit UTC-Tagesindex um.

    WARUM: Der Index ist der Eröffnungszeitpunkt der Tageskerze (00:00 UTC).
    Der Schlusskurs der Zeile T ist damit der Kurs um 23:59:59 UTC des Tages T.
    Sortierung/Duplikate/Lücken werden hier bewusst NICHT behandelt, damit
    validate.py sie in den Rohdaten findet und clean.py sie protokolliert korrigiert.
    """
    index = pd.to_datetime(_open_time_ms(raw["open_time"]), unit="ms", utc=True)
    df = raw[["open", "high", "low", "close", "volume"]].astype(float)
    df.index = pd.DatetimeIndex(index, name="date")
    return df
