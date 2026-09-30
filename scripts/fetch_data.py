"""Datenpipeline: Rohdaten laden → validieren → bereinigen → zusammenführen → speichern.

Aufruf:  uv run python scripts/fetch_data.py [--refresh]

WARUM ein Skript: Die ganze Pipeline steht in einer Datei in fester Reihenfolge
und ist dadurch für das Team Schritt für Schritt nachvollziehbar.
Ohne --refresh werden gecachte Rohdaten aus data/raw verwendet.
"""

import argparse

import pandas as pd

from bot.config import RESULTS_DIR, load_settings
from bot.data import clean, dataset, validate
from bot.data.loader_binance import load_binance, parse_binance
from bot.data.loader_bitstamp import load_bitstamp, parse_bitstamp
from bot.data.loader_feargreed import load_feargreed, parse_feargreed


def main() -> None:
    """Führt die Pipeline aus und gibt eine kurze Zusammenfassung aus."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="Rohdaten neu herunterladen (Cache ignorieren)")
    args = parser.parse_args()
    settings = load_settings()

    # 1) Rohdaten (Cache oder Download) und in Zahlen/UTC umwandeln
    binance_raw = parse_binance(load_binance(settings, args.refresh))
    bitstamp_raw = parse_bitstamp(load_bitstamp(settings, args.refresh))
    fg_raw = parse_feargreed(load_feargreed(settings, args.refresh))

    # 2) Validierung auf Rohdaten (vor Bereinigung)
    checks = {
        "Binance BTC/USDT (Hauptdaten)": (binance_raw, validate.check_ohlcv(binance_raw, settings)),
        "Bitstamp BTC/USD (Aufwärmdaten)": (bitstamp_raw, validate.check_ohlcv(bitstamp_raw, settings)),
        "Fear & Greed Index": (fg_raw, validate.check_feargreed(fg_raw)),
    }
    overlap = validate.overlap_stats(
        bitstamp_raw, binance_raw, settings["binance_start"], settings["eval_start"] - pd.Timedelta(days=1)
    )

    # 3) Bereinigung mit Protokoll
    binance, log_bn = clean.clean_ohlcv(binance_raw, "binance")
    bitstamp, log_bs = clean.clean_ohlcv(bitstamp_raw, "bitstamp")
    fear_greed, log_fg = clean.clean_feargreed(fg_raw)
    cleaning_log = pd.concat([log_bn, log_bs, log_fg], ignore_index=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    cleaning_log.to_csv(RESULTS_DIR / "cleaning_log.csv", index=False, lineterminator="\n")

    # 4) Zusammenführen und speichern
    merged = dataset.merge_sources(bitstamp, binance, fear_greed, settings)
    dataset.save_dataset(merged)
    validate.write_report(RESULTS_DIR / "data_validation.md", checks, overlap, cleaning_log)

    # 5) Zusammenfassung
    print("Geladene Tage pro Quelle (roh):")
    for title, (data, _) in checks.items():
        print(f"  {title}: {len(data)} Tage, {data.index.min():%Y-%m-%d} bis {data.index.max():%Y-%m-%d}")
    print("Zeilen im Datensatz pro Quelle:", merged["source"].value_counts().to_dict())
    print(f"Überlappung: mittl. |Abw.| {overlap['mean_abs_pct']:.3f} %, max. {overlap['max_abs_pct']:.3f} % "
          f"({overlap['max_date']:%Y-%m-%d})")
    for title, (_, result) in checks.items():
        print(f"  {title}: " + ", ".join(f"{k}={len(v)}" for k, v in result.items()))
    print(f"Korrekturen: {len(cleaning_log)}. Bericht: results/data_validation.md")


if __name__ == "__main__":
    main()
