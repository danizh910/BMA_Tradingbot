"""Datenvalidierung: prüft Rohdaten auf Fehler und schreibt results/data_validation.md.

WARUM: Fehlerhafte Daten führen zu falschen Backtest-Ergebnissen, ohne dass
der Code abstürzt («stille» Fehler). Die Prüfungen laufen auf den Rohdaten
VOR der Bereinigung, damit sichtbar ist, was clean.py korrigieren musste.
"""

from pathlib import Path

import pandas as pd

PRICE_COLS = ["open", "high", "low", "close"]
WARNING_CHECKS = {"ausreisser"}  # nur Warnung, kein Datenfehler
MAX_LISTED_DATES = 15


def true_range(df: pd.DataFrame) -> pd.Series:
    """True Range = max(High − Low, |High − Close_vortag|, |Low − Close_vortag|)."""
    prev_close = df["close"].shift(1)
    return pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()], axis=1
    ).max(axis=1)


def check_ohlcv(df: pd.DataFrame, settings: dict) -> dict[str, pd.DatetimeIndex]:
    """Führt alle OHLCV-Prüfungen durch und gibt pro Prüfung die betroffenen Tage zurück.

    WARUM Ausreisser-Definition: High − Low > Faktor × ATR. Die ATR wird aus den
    VORTAGEN berechnet (shift(1)), damit ein extremer Tag seine eigene Schwelle
    nicht selbst erhöht. Ausreisser sind nur Warnungen, echte Kurssprünge
    (z. B. März 2020) sind in Krypto möglich. Die ATR läuft über die
    vorhandenen Zeilen (ohne asfreq), damit eine Datenlücke die Prüfung
    nicht für die folgenden atr_days Tage ausschaltet (siehe KI-Fehlerlog #1).
    """
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
    unique = df[~df.index.duplicated(keep="first")].sort_index()
    body_max = unique[["open", "close"]].max(axis=1)
    body_min = unique[["open", "close"]].min(axis=1)
    cfg = settings["validation"]
    atr = true_range(unique).rolling(cfg["atr_days"]).mean().shift(1)
    return {
        "fehlende_tage": full_range.difference(df.index),
        "duplikate": df.index[df.index.duplicated()],
        "preise_<=_0": unique.index[(unique[PRICE_COLS] <= 0).any(axis=1)],
        "high_<_max(open,close)": unique.index[unique["high"] < body_max],
        "low_>_min(open,close)": unique.index[unique["low"] > body_min],
        "volumen_<_0": unique.index[unique["volume"] < 0],
        "ausreisser": unique.index[(unique["high"] - unique["low"]) > cfg["outlier_atr_multiple"] * atr],
    }


def check_feargreed(fg: pd.Series) -> dict[str, pd.DatetimeIndex]:
    """Findet fehlende Tage und Duplikate im F&G-Index zwischen erstem und letztem Wert."""
    full_range = pd.date_range(fg.index.min(), fg.index.max(), freq="D")
    return {
        "fehlende_tage": full_range.difference(fg.index),
        "duplikate": fg.index[fg.index.duplicated()],
    }


def overlap_stats(bitstamp: pd.DataFrame, binance: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    """Vergleicht die Schlusskurse Bitstamp (USD) und Binance (USDT) im Überlappungszeitraum.

    WARUM: Die Aufwärmdaten stammen von einer anderen Börse und in USD statt USDT.
    Die Abweichung zeigt, wie gross der «Sprung» an der Nahtstelle ist.
    Relative Abweichung = Bitstamp / Binance − 1.
    """
    joined = pd.concat(
        [bitstamp["close"].rename("bitstamp"), binance["close"].rename("binance")], axis=1, join="inner"
    ).loc[start:end]
    rel = joined["bitstamp"] / joined["binance"] - 1
    return {
        "start": start, "end": end, "n_days": len(joined),
        "mean_abs_pct": rel.abs().mean() * 100,
        "mean_signed_pct": rel.mean() * 100,
        "max_abs_pct": rel.abs().max() * 100,
        "max_date": rel.abs().idxmax(),
    }


def _fmt_dates(dates: pd.DatetimeIndex) -> str:
    """Formatiert Datumsliste kurz für den Bericht (max. MAX_LISTED_DATES Einträge)."""
    shown = ", ".join(d.strftime("%Y-%m-%d") for d in dates[:MAX_LISTED_DATES])
    return shown + (f" … (+{len(dates) - MAX_LISTED_DATES})" if len(dates) > MAX_LISTED_DATES else "")


def _section(title: str, df_or_series, checks: dict[str, pd.DatetimeIndex]) -> list[str]:
    """Erzeugt einen Markdown-Abschnitt mit Prüftabelle für eine Datenquelle."""
    lines = [
        f"## {title}", "",
        f"Zeitraum: {df_or_series.index.min():%Y-%m-%d} bis {df_or_series.index.max():%Y-%m-%d}, "
        f"{len(df_or_series)} Zeilen (roh)", "",
        "| Prüfung | Anzahl | Status | Tage |", "|---|---:|---|---|",
    ]
    for name, dates in checks.items():
        if len(dates) == 0:
            status = "OK"
        else:
            status = "WARNUNG" if name in WARNING_CHECKS else "FEHLER"
        lines.append(f"| {name} | {len(dates)} | {status} | {_fmt_dates(dates)} |")
    return lines + [""]


def write_report(
    path: Path,
    sources: dict[str, tuple],
    overlap: dict,
    cleaning_log: pd.DataFrame,
) -> None:
    """Schreibt den Validierungsbericht als Markdown.

    sources: Titel -> (Daten, Prüfergebnis). WARUM Markdown: im Repo lesbar
    und direkt in die BMA-Dokumentation übernehmbar.
    """
    lines = ["# Datenvalidierung", "", "Automatisch erzeugt durch `scripts/fetch_data.py`. Prüfung auf Rohdaten vor der Bereinigung.", ""]
    for title, (data, checks) in sources.items():
        lines += _section(title, data, checks)

    lines += [
        "## Überlappung Bitstamp (BTC/USD) vs. Binance (BTC/USDT)", "",
        f"Zeitraum {overlap['start']:%Y-%m-%d} bis {overlap['end']:%Y-%m-%d}, {overlap['n_days']} gemeinsame Tage. "
        "Relative Abweichung der Schlusskurse = Bitstamp / Binance − 1.", "",
        "| Kennzahl | Wert |", "|---|---:|",
        f"| mittlere absolute Abweichung | {overlap['mean_abs_pct']:.3f} % |",
        f"| mittlere Abweichung (mit Vorzeichen) | {overlap['mean_signed_pct']:+.3f} % |",
        f"| maximale absolute Abweichung | {overlap['max_abs_pct']:.3f} % (am {overlap['max_date']:%Y-%m-%d}) |",
        "",
        "## Bereinigung (clean.py)", "",
        f"Anzahl Korrekturen: {len(cleaning_log)}. Details: `results/cleaning_log.csv`.", "",
    ]
    if len(cleaning_log):
        counts = cleaning_log.groupby(["source", "field"]).size()
        lines += ["| Quelle | Feld | Korrekturen |", "|---|---|---:|"]
        lines += [f"| {s} | {f} | {n} |" for (s, f), n in counts.items()]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
