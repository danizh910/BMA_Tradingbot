"""Cache für Rohdaten mit SHA256-Prüfsummen.

WARUM: Rohdaten werden einmal geladen und unverändert als CSV gespeichert.
Die Prüfsumme in docs/data_checksums.txt macht nachweisbar, dass alle
Auswertungen auf denselben Rohdaten beruhen.
"""

import hashlib
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from bot.config import DOCS_DIR, RAW_DIR

CHECKSUM_FILE = DOCS_DIR / "data_checksums.txt"


def sha256_of(path: Path) -> str:
    """Berechnet die SHA256-Prüfsumme einer Datei (WARUM: Nachweis der Unverändertheit)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_checksums() -> dict[str, str]:
    """Liest die Prüfsummendatei im Format '<sha256>  <dateiname>' in ein Dict."""
    if not CHECKSUM_FILE.exists():
        return {}
    result = {}
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            result[name.strip()] = digest
    return result


def _record_checksum(path: Path) -> None:
    """Schreibt/aktualisiert die Prüfsumme einer Rohdatei (sortiert, damit Diffs lesbar bleiben)."""
    checksums = _read_checksums()
    checksums[path.name] = sha256_of(path)
    lines = [f"{digest}  {name}" for name, digest in sorted(checksums.items())]
    CHECKSUM_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_raw_csv(filename: str, fetch_fn: Callable[[], pd.DataFrame], refresh: bool = False) -> pd.DataFrame:
    """Gibt Rohdaten aus dem Cache zurück oder lädt sie über fetch_fn neu.

    WARUM: Ohne --refresh wird nie neu geladen, damit sich die Datenbasis nicht
    unbemerkt ändert. Weicht eine gecachte Datei von ihrer gespeicherten
    Prüfsumme ab, wird abgebrochen statt mit veränderten Daten weiterzurechnen.
    Alle Werte werden als Text gelesen, damit nichts stillschweigend konvertiert wird.
    """
    path = RAW_DIR / filename
    if path.exists() and not refresh:
        recorded = _read_checksums().get(filename)
        if recorded is None:
            _record_checksum(path)
        elif recorded != sha256_of(path):
            raise ValueError(f"Prüfsumme von {filename} stimmt nicht. Datei verändert? Mit --refresh neu laden.")
        return pd.read_csv(path, dtype=str)

    df = fetch_fn()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    # lineterminator fix: gleiche Bytes (und Prüfsumme) auf Windows, macOS und Linux
    df.to_csv(path, index=False, lineterminator="\n")
    _record_checksum(path)
    return pd.read_csv(path, dtype=str)
