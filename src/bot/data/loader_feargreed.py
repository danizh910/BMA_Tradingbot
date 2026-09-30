"""Lädt den Crypto Fear & Greed Index von alternative.me (verfügbar ab 2018-02-01).

WARUM: Der Index ist ein möglicher Stimmungsindikator für spätere Strategien.
Die zeitliche Verschiebung (Wert T erst ab Schluss T+1 nutzbar) passiert in dataset.py.
"""

import pandas as pd
import requests

from bot.data.raw_cache import load_raw_csv

RAW_FILE = "feargreed.csv"
TIMEOUT_S = 30


def fetch(settings: dict) -> pd.DataFrame:
    """Lädt die gesamte Historie (limit=0) und gibt die Einträge unverändert als Tabelle zurück."""
    resp = requests.get(settings["sources"]["feargreed_api"], timeout=TIMEOUT_S)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("metadata", {}).get("error"):
        raise RuntimeError(f"Fear & Greed API meldet Fehler: {payload['metadata']['error']}")
    return pd.DataFrame(payload["data"])


def load_feargreed(settings: dict, refresh: bool = False) -> pd.DataFrame:
    """Gibt die F&G-Rohdaten zurück (aus dem Cache oder frisch geladen)."""
    return load_raw_csv(RAW_FILE, lambda: fetch(settings), refresh)


def parse_feargreed(raw: pd.DataFrame) -> pd.Series:
    """Wandelt Rohdaten in eine aufsteigend sortierte Serie (Index = Datum UTC, Wert 0–100).

    WARUM: Die API liefert die neuesten Werte zuerst; für Zeitreihen braucht es
    aufsteigende Reihenfolge. Duplikate/Lücken werden in validate/clean behandelt.
    """
    index = pd.DatetimeIndex(pd.to_datetime(raw["timestamp"].astype("int64"), unit="s", utc=True), name="date")
    return pd.Series(raw["value"].astype(float).to_numpy(), index=index, name="fear_greed").sort_index()
