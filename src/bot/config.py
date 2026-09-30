"""Zentrale Konfiguration: lädt config/settings.yaml und definiert die Projektpfade.

WARUM: Laut Projektregel stehen alle festen Werte in settings.yaml. So sind
Parameter an genau einer Stelle sichtbar und nicht im Code verstreut.
"""

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = ROOT / "config" / "settings.yaml"
STRATEGIES_FILE = ROOT / "config" / "strategies.yaml"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs"

DATE_KEYS = ("binance_start", "warmup_start", "eval_start", "is_end", "oos_start", "oos_end")


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    """Liest settings.yaml und wandelt alle Datumswerte in UTC-Zeitstempel um.

    WARUM: Einheitlich UTC verhindert Verschiebungen um einen Tag durch lokale
    Zeitzonen. Die Prüfung IS/OOS stellt sicher, dass zwischen den beiden
    Zeiträumen weder eine Lücke noch eine Überlappung entsteht.
    """
    with open(path, encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    for key in DATE_KEYS:
        settings[key] = pd.Timestamp(str(settings[key]), tz="UTC")

    if settings["oos_start"] != settings["is_end"] + pd.Timedelta(days=1):
        raise ValueError("oos_start muss genau einen Tag nach is_end liegen (keine Lücke/Überlappung).")
    if not settings["warmup_start"] < settings["binance_start"] < settings["eval_start"] <= settings["is_end"]:
        raise ValueError("Reihenfolge warmup_start < binance_start < eval_start <= is_end verletzt.")
    return settings


def load_strategy_config(path: Path = STRATEGIES_FILE) -> dict:
    """Liest config/strategies.yaml (Standardparameter und Grids aller Strategien).

    WARUM: Strategie-Parameter gehören laut Projektregel in eine Config-Datei,
    damit Standardwerte und Optimierungsbereiche ohne Codeänderung sichtbar sind.
    """
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
