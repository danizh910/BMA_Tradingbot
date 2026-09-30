"""Zusammenführen der Quellen und kontrollierter Zugriff auf die Zeiträume (Splits).

WARUM: Alle späteren Module holen Daten ausschliesslich über get_data().
So gelten die Split-Grenzen und die Out-of-Sample-Sperre überall gleich.
"""

import inspect
import os
import subprocess
from datetime import datetime, timezone

import pandas as pd

from bot.config import DOCS_DIR, PROCESSED_DIR, ROOT, load_settings

DATASET_FILE = PROCESSED_DIR / "dataset.csv"
OOS_LOG_FILE = DOCS_DIR / "oos_runs.log"
OOS_ENV_VAR = "BMA_ALLOW_OOS"
LOCKED_SPLITS = {"oos", "full"}
SPLITS = {"warmup_is", "is", "oos", "full"}


def merge_sources(bitstamp: pd.DataFrame, binance: pd.DataFrame, fear_greed: pd.Series, settings: dict) -> pd.DataFrame:
    """Führt Aufwärmdaten (Bitstamp), Binance-OHLCV und F&G zu einer Tabelle zusammen.

    WARUM:
    - Bitstamp nur für Tage VOR binance_start (reine Aufwärmdaten für Indikatoren).
    - Spalte "source" dokumentiert pro Zeile die Herkunft.
    - F&G mit Datum T wird erst am Tagesschluss T+1 verwendet: shift(1).
      Grund: Der genaue Veröffentlichungszeitpunkt und die zugrunde liegenden
      Daten des Werts T sind nicht exakt dokumentiert. Konservative Annahme:
      lieber einen Tag zu spät als ein möglicher Look-Ahead.
      Die Zeile T enthält also den F&G-Wert vom Vortag T−1.
    Prüft am Ende, dass der Tagesindex lückenlos und ohne Duplikate ist.
    """
    one_day = pd.Timedelta(days=1)
    warmup = bitstamp.loc[settings["warmup_start"]: settings["binance_start"] - one_day]
    main = binance.loc[settings["binance_start"]: settings["oos_end"]]
    df = pd.concat([
        warmup.assign(source=settings["warmup_source"]),
        main.assign(source=f"binance_{settings['symbol'].lower()}"),
    ])

    expected = pd.date_range(df.index.min(), df.index.max(), freq="D", name="date")
    if not df.index.equals(expected):
        raise ValueError("Zusammengeführter Index ist nicht lückenlos/eindeutig – Bereinigung prüfen.")
    df = df.asfreq("D")
    df["fear_greed"] = fear_greed.reindex(df.index).shift(1)
    return df


def save_dataset(df: pd.DataFrame) -> None:
    """Speichert den zusammengeführten Datensatz als CSV in data/processed."""
    DATASET_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATASET_FILE, lineterminator="\n")


def load_dataset() -> pd.DataFrame:
    """Liest den gespeicherten Datensatz (UTC-Tagesindex).

    WARUM: get_data() soll nie selbst Daten aus dem Internet laden; das macht
    ausschliesslich scripts/fetch_data.py, damit jede Datenänderung bewusst geschieht.
    """
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"{DATASET_FILE} fehlt. Zuerst `uv run python scripts/fetch_data.py` ausführen.")
    df = pd.read_csv(DATASET_FILE, index_col="date")
    df.index = pd.to_datetime(df.index, utc=True)
    return df.asfreq("D")


def _git_commit() -> str:
    """Gibt den aktuellen Git-Commit-Hash zurück, mit «+dirty» bei uncommitteten Änderungen.

    WARUM: Ein OOS-Lauf muss einer exakten Codeversion zugeordnet werden können.
    """
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unbekannt"
    return head + ("+dirty" if dirty else "")


def _check_oos_access(split: str) -> None:
    """Out-of-Sample-Sperre: Fehler ohne BMA_ALLOW_OOS=1, sonst Protokolleintrag.

    WARUM: Wer OOS-Daten während der Entwicklung ansieht, optimiert unbewusst
    darauf – der OOS-Test wäre dann wertlos. Jeder Zugriff wird mit Zeitstempel,
    Commit und Aufrufer in docs/oos_runs.log protokolliert.
    Die Systemzeit wird hier NUR für das Protokoll verwendet, nie in der Logik.
    """
    if os.environ.get(OOS_ENV_VAR) != "1":
        raise PermissionError(
            f"Zugriff auf Split '{split}' gesperrt (Out-of-Sample). Nur mit ausdrücklicher Freigabe: {OOS_ENV_VAR}=1."
        )
    caller = inspect.stack()[2]  # 0 = diese Funktion, 1 = get_data, 2 = Aufrufer
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = f"{timestamp}\tsplit={split}\tcommit={_git_commit()}\tcaller={caller.filename}:{caller.lineno} ({caller.function})\n"
    with open(OOS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def get_data(split: str, dataset: pd.DataFrame | None = None, settings: dict | None = None) -> pd.DataFrame:
    """Gibt den gewünschten Zeitraum zurück.

    split:
    - "warmup_is": alles bis und mit is_end, inkl. Aufwärmdaten
    - "is":        eval_start bis is_end (In-Sample)
    - "oos":       oos_start bis oos_end (gesperrt)
    - "full":      alles inkl. Aufwärmdaten bis oos_end (gesperrt)
    dataset: optional ein bereits geladener Datensatz (v. a. für Tests), sonst data/processed.
    WARUM: Einheitliche Grenzen für alle Module; .loc mit Datum schliesst beide Enden ein.
    """
    if split not in SPLITS:
        raise ValueError(f"Unbekannter Split '{split}'. Erlaubt: {sorted(SPLITS)}")
    if split in LOCKED_SPLITS:
        _check_oos_access(split)
    settings = settings or load_settings()
    df = dataset if dataset is not None else load_dataset()
    bounds = {
        "warmup_is": (None, settings["is_end"]),
        "is": (settings["eval_start"], settings["is_end"]),
        "oos": (settings["oos_start"], settings["oos_end"]),
        "full": (None, settings["oos_end"]),
    }
    start, end = bounds[split]
    return df.loc[start:end].copy()
