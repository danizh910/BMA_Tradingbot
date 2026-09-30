"""Streamlit-Dashboard der BMA. Start: uv run streamlit run dashboard/app.py

WARUM: Visuelle Kontrolle der Daten und später der Ergebnisse für das Team
und die Präsentation. Aktuell ist nur die Seite «Daten» umgesetzt.
Die OOS-Sperre gilt auch hier: ohne BMA_ALLOW_OOS=1 werden nur Daten bis is_end gezeigt.
"""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from bot.config import load_settings
from bot.data.dataset import OOS_ENV_VAR, get_data

PAGES = ["Daten", "Strategien", "Optimierung", "Out-of-Sample", "Marktphasen", "KI-Fehlerlog"]
BULL_COLOR = "rgba(46, 160, 67, 0.12)"
BEAR_COLOR = "rgba(218, 54, 51, 0.12)"
WARMUP_COLOR = "rgba(128, 128, 128, 0.25)"


def regime_segments(is_bull: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, bool]]:
    """Fasst aufeinanderfolgende Tage gleicher Marktphase zu Abschnitten (Start, Ende, bull?) zusammen.

    WARUM: Ein farbiges Rechteck pro Abschnitt statt pro Tag hält die Grafik schnell.
    """
    block_id = (is_bull != is_bull.shift()).cumsum()
    return [(g.index[0], g.index[-1] + pd.Timedelta(days=1), bool(g.iloc[0])) for _, g in is_bull.groupby(block_id)]


def page_data(settings: dict) -> None:
    """Seite «Daten»: Kurs (log) mit 200-Tage-Linie, Bull/Bear-Phasen, F&G-Index, Aufwärmbereich grau.

    WARUM Bull/Bear-Definition: Schlusskurs über (bull) bzw. unter (bear) dem
    gleitenden Durchschnitt über regime_ma_days Tage (kausales Fenster, center=False).
    Die Einfärbung ist eine Beschreibung, kein Handelssignal.
    """
    split = "full" if os.environ.get(OOS_ENV_VAR) == "1" else "warmup_is"
    df = get_data(split)
    ma_days = settings["regime_ma_days"]
    ma = df["close"].rolling(ma_days, center=False).mean()
    has_ma = ma.notna()
    is_bull = (df["close"] > ma)[has_ma]

    st.header("Daten")
    st.caption(
        f"Anzeige: Split «{split}» ({df.index.min():%Y-%m-%d} bis {df.index.max():%Y-%m-%d}). "
        f"Grau = Aufwärmdaten vor {settings['eval_start']:%Y-%m-%d}. Grün/Rot = Kurs über/unter {ma_days}-Tage-Linie."
    )

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="Schlusskurs", line=dict(color="#1f3b73", width=1.2)), 1, 1)
    fig.add_trace(go.Scatter(x=df.index, y=ma, name=f"{ma_days}-Tage-Linie", line=dict(color="#e08a00", width=1.5)), 1, 1)
    fig.add_trace(go.Scatter(x=df.index, y=df["fear_greed"], name="Fear & Greed (Vortag)",
                             line=dict(color="#6a4c93", width=1)), 2, 1)

    for start, end, bull in regime_segments(is_bull):
        fig.add_vrect(x0=start, x1=end, fillcolor=BULL_COLOR if bull else BEAR_COLOR, line_width=0, row=1, col=1)
    fig.add_vrect(x0=df.index.min(), x1=settings["eval_start"], fillcolor=WARMUP_COLOR, line_width=0,
                  annotation_text="Aufwärmphase", annotation_position="top left", row="all", col=1)

    fig.update_yaxes(type="log", title_text="USD(T), log", row=1, col=1)
    fig.update_yaxes(range=[0, 100], title_text="F&G", row=2, col=1)
    fig.update_layout(height=700, hovermode="x unified", legend=dict(orientation="h", y=1.05), margin=dict(t=40))
    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    col1.subheader("Zeilen pro Quelle")
    col1.dataframe(df["source"].value_counts().rename("Tage"))
    col2.subheader("Anteil Marktphasen (ab erster MA)")
    col2.dataframe(is_bull.map({True: "Bull", False: "Bear"}).value_counts().rename("Tage"))


def main() -> None:
    """Navigation über die Seitenleiste; noch nicht umgesetzte Seiten zeigen einen Platzhalter."""
    st.set_page_config(page_title="BMA BTC Trading-Bot", layout="wide")
    settings = load_settings()
    page = st.sidebar.radio("Seite", PAGES)
    if page == "Daten":
        page_data(settings)
    else:
        st.header(page)
        st.info("Platzhalter – wird in einem späteren Projektschritt umgesetzt.")


main()
