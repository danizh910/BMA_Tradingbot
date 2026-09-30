"""Bereinigung der Zeitreihen: lückenloser Tagesindex, Forward-Fill, Protokoll jeder Korrektur.

WARUM: Backtests brauchen einen lückenlosen Tagesindex, sonst werden Renditen
über mehrere Tage fälschlich als Tagesrendite gezählt. Es wird NIE ein
Backward-Fill verwendet, weil dieser Informationen aus der Zukunft in die
Vergangenheit kopieren würde (Look-Ahead).
"""

import pandas as pd

PRICE_COLS = ["open", "high", "low", "close"]
LOG_COLUMNS = ["date", "source", "field", "old_value", "new_value"]


def clean_ohlcv(df: pd.DataFrame, source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entfernt Duplikate, erzeugt einen vollständigen Tagesindex und füllt fehlende Tage.

    WARUM:
    - Duplikate: die erste Zeile gilt, weitere werden entfernt (protokolliert).
    - Fehlender Tag: Open/High/Low/Close = letzter bekannter Schlusskurs
      (Forward-Fill, «flache Kerze» ohne erfundene Schwankung), Volumen = 0,
      weil an diesem Tag kein Handel belegt ist.
    Gibt die bereinigten Daten und ein Korrekturprotokoll (Datum, Feld, alt, neu) zurück.
    """
    log = []
    df = df.sort_index()
    duplicated = df.index.duplicated(keep="first")
    for date in df.index[duplicated]:
        log.append((date, source, "zeile", "duplikat", "entfernt"))
    df = df[~duplicated].asfreq("D")

    # Letzter bekannter Schlusskurs VOR dem Tag: shift(1) dann ffill – nie bfill.
    prev_close = df["close"].shift(1).ffill()
    for col in PRICE_COLS:
        missing = df[col].isna()
        for date in df.index[missing]:
            log.append((date, source, col, None, prev_close[date]))
        df.loc[missing, col] = prev_close[missing]

    missing_vol = df["volume"].isna()
    for date in df.index[missing_vol]:
        log.append((date, source, "volume", None, 0.0))
    df.loc[missing_vol, "volume"] = 0.0

    return df, pd.DataFrame(log, columns=LOG_COLUMNS)


def clean_feargreed(fg: pd.Series, source: str = "feargreed") -> tuple[pd.Series, pd.DataFrame]:
    """Erzeugt einen lückenlosen Tagesindex für den F&G-Index und füllt Lücken per Forward-Fill.

    WARUM: Forward-Fill ist kausal (nur der letzte bekannte Wert wird verwendet).
    Vor dem ersten verfügbaren Wert bleibt der Index leer (NaN), weil kein bfill erfolgt.
    """
    log = []
    fg = fg.sort_index()
    duplicated = fg.index.duplicated(keep="first")
    for date in fg.index[duplicated]:
        log.append((date, source, "zeile", "duplikat", "entfernt"))
    fg = fg[~duplicated].asfreq("D")
    filled = fg.ffill()
    for date in fg.index[fg.isna()]:
        log.append((date, source, "fear_greed", None, filled[date]))
    return filled, pd.DataFrame(log, columns=LOG_COLUMNS)
