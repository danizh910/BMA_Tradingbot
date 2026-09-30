"""Lädt BTC/USD-Tagesdaten von Bitstamp (öffentliche OHLC-API).

WARUM: Binance hat erst ab 2017-08-17 Daten. Für Indikatoren wie den
200-Tage-Durchschnitt braucht es vorher Aufwärmdaten. Bitstamp-Daten werden
nur für Tage VOR binance_start verwendet (siehe dataset.py). Bis Ende 2017
wird geladen, damit die Überlappung mit Binance geprüft werden kann.
Bei einem API-Fehler wird bewusst KEINE andere Quelle gewählt (Teamentscheid).
"""

import pandas as pd
import requests

from bot.data.raw_cache import load_raw_csv

RAW_FILE = "bitstamp_btcusd_1d.csv"
PAGE_LIMIT = 1000  # technisches Maximum der API pro Aufruf
DAY_SECONDS = 86400
TIMEOUT_S = 30


def fetch(settings: dict) -> pd.DataFrame:
    """Lädt Tageskerzen von warmup_start bis zum Tag vor eval_start, paginiert.

    WARUM: Das Ende (Tag vor eval_start) deckt die Überlappung
    binance_start..eval_start-1 ab, die in validate.py verglichen wird.
    """
    start = int(settings["warmup_start"].timestamp())
    end = int((settings["eval_start"] - pd.Timedelta(days=1)).timestamp())
    rows = []
    try:
        while start <= end:
            params = {"step": DAY_SECONDS, "limit": PAGE_LIMIT, "start": start}
            resp = requests.get(settings["sources"]["bitstamp_api"], params=params, timeout=TIMEOUT_S)
            resp.raise_for_status()
            batch = resp.json()["data"]["ohlc"]
            if not batch:
                break
            rows.extend(r for r in batch if int(r["timestamp"]) <= end)
            start = int(batch[-1]["timestamp"]) + DAY_SECONDS
    except (requests.RequestException, KeyError) as err:
        raise RuntimeError(
            "Bitstamp-API nicht nutzbar. Laut Projektregel: stoppen und Team fragen, "
            f"keine andere Quelle eigenmächtig wählen. Fehler: {err}"
        ) from err
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def load_bitstamp(settings: dict, refresh: bool = False) -> pd.DataFrame:
    """Gibt die Bitstamp-Rohdaten zurück (aus dem Cache oder frisch geladen)."""
    return load_raw_csv(RAW_FILE, lambda: fetch(settings), refresh)


def parse_bitstamp(raw: pd.DataFrame) -> pd.DataFrame:
    """Wandelt Rohdaten in OHLCV mit UTC-Tagesindex um (Zeitstempel in Sekunden, 00:00 UTC)."""
    df = raw[["open", "high", "low", "close", "volume"]].astype(float)
    df.index = pd.DatetimeIndex(pd.to_datetime(raw["timestamp"].astype("int64"), unit="s", utc=True), name="date")
    return df
