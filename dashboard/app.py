"""Streamlit-Dashboard der BMA. Start: uv run streamlit run dashboard/app.py

WARUM: Visuelle Kontrolle der Daten und Ergebnisse für das Team und die Präsentation.
Die Seiten Strategien/Optimierung/Marktphasen lesen die Resultate aus results/
(erzeugt von run_optimization.py und run_insample.py) und rechnen nichts neu.
Die OOS-Sperre gilt auch hier: ohne BMA_ALLOW_OOS=1 werden nur Daten bis is_end gezeigt.
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml
from plotly.subplots import make_subplots

from bot.analysis.evaluation import BEST_PARAMS_FILE, BENCHMARK
from bot.analysis.regimes import classify_regimes
from bot.config import DOCS_DIR, RESULTS_DIR, load_settings
from bot.data.dataset import OOS_ENV_VAR, get_data
from bot.strategies import STRATEGIES

PAGES = ["Daten", "Strategien", "Optimierung", "Out-of-Sample", "Marktphasen", "KI-Fehlerlog"]
BULL_COLOR = "rgba(46, 160, 67, 0.12)"
BEAR_COLOR = "rgba(218, 54, 51, 0.12)"
WARMUP_COLOR = "rgba(128, 128, 128, 0.25)"
PERCENT_COLUMNS = ["total_return", "cagr", "volatility", "max_drawdown", "hit_rate", "avg_exposure",
                   "total_costs", "share_days"]


def regime_segments(is_bull: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, bool]]:
    """Fasst aufeinanderfolgende Tage gleicher Marktphase zu Abschnitten (Start, Ende, bull?) zusammen.

    WARUM: Ein farbiges Rechteck pro Abschnitt statt pro Tag hält die Grafik schnell.
    """
    block_id = (is_bull != is_bull.shift()).cumsum()
    return [(g.index[0], g.index[-1] + pd.Timedelta(days=1), bool(g.iloc[0])) for _, g in is_bull.groupby(block_id)]


def read_csv_result(path, **kwargs) -> pd.DataFrame | None:
    """Liest eine Resultat-CSV. Fehlt sie, erscheint ein Hinweis, welches Skript sie erzeugt."""
    if not path.exists():
        st.warning(f"{path.relative_to(RESULTS_DIR.parent)} fehlt. Zuerst run_optimization.py und run_insample.py ausführen.")
        return None
    return pd.read_csv(path, **kwargs)


def as_percent(df: pd.DataFrame) -> pd.DataFrame:
    """Formatiert Anteils-Spalten als Prozent (nur für die Anzeige)."""
    out = df.copy()
    for col in PERCENT_COLUMNS:
        if col in out:
            out[col] = (out[col] * 100).round(1).astype(str) + " %"
    return out


def page_data(settings: dict) -> None:
    """Seite «Daten»: Kurs (log) mit 200-Tage-Linie, Bull/Bear-Phasen, F&G-Index, Aufwärmbereich grau.

    Bull/Bear wie in regimes.py: Tag t ist bull, wenn Close(t−1) > SMA200(t−1).
    Die Einfärbung ist eine Beschreibung, kein Handelssignal.
    """
    split = "full" if os.environ.get(OOS_ENV_VAR) == "1" else "warmup_is"
    df = get_data(split)
    ma_days = settings["regime_ma_days"]
    ma = df["close"].rolling(ma_days, center=False).mean()
    regimes = classify_regimes(df, settings).dropna()
    is_bull = regimes == "bull"

    st.header("Daten")
    st.caption(
        f"Anzeige: Split «{split}» ({df.index.min():%Y-%m-%d} bis {df.index.max():%Y-%m-%d}). "
        f"Grau = Aufwärmdaten vor {settings['eval_start']:%Y-%m-%d}. "
        f"Grün/Rot = Bull/Bear (Schlusskurs des Vortags über/unter der {ma_days}-Tage-Linie des Vortags)."
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
    col2.dataframe(regimes.value_counts().rename("Tage"))


def page_strategies() -> None:
    """Seite «Strategien»: Kennzahlen aller Varianten, Equity-Kurven, Kosten-Sensitivität, Trades (In-Sample)."""
    st.header("Strategien (In-Sample)")
    summary = read_csv_result(RESULTS_DIR / "insample_summary.csv")
    equity = read_csv_result(RESULTS_DIR / "insample_equity.csv", index_col=0, parse_dates=True)
    costs = read_csv_result(RESULTS_DIR / "insample_costs.csv")
    trades = read_csv_result(RESULTS_DIR / "insample_trades.csv")
    if summary is None or equity is None or costs is None or trades is None:
        return

    total = summary[summary["scope"] == "gesamt"].drop(columns="scope").set_index("variant")
    st.subheader("Kennzahlen gesamt")
    st.dataframe(as_percent(total.round(3)), width="stretch")

    st.subheader("Equity-Kurven (Start = 1, log-Skala)")
    chosen = st.multiselect("Varianten", list(equity.columns),
                            default=[c for c in equity.columns if "Standard" in c or c == BENCHMARK])
    fig = go.Figure()
    for name in chosen:
        width = 2.5 if name == BENCHMARK else 1.3
        fig.add_trace(go.Scatter(x=equity.index, y=equity[name], name=name, line=dict(width=width)))
    fig.update_yaxes(type="log")
    fig.update_layout(height=520, hovermode="x unified")
    st.plotly_chart(fig, width="stretch")

    st.subheader("Kosten-Sensitivität: Sharpe Ratio je Gebühr pro Positionsänderung")
    st.dataframe(costs.pivot(index="variant", columns="cost_per_trade", values="sharpe").round(3), width="stretch")

    st.subheader("Trades")
    variant = st.selectbox("Variante", list(total.index))
    st.dataframe(trades[trades["variant"] == variant].drop(columns="variant"), width="stretch")


def page_optimization() -> None:
    """Seite «Optimierung»: Heatmaps, Standard vs. optimiert, Plateau-Check, Deflated Sharpe Ratio."""
    st.header("Optimierung (nur In-Sample)")
    if not BEST_PARAMS_FILE.exists():
        st.warning("best_params.yaml fehlt. Zuerst scripts/run_optimization.py ausführen.")
        return
    best = yaml.safe_load(BEST_PARAMS_FILE.read_text(encoding="utf-8"))
    overview = pd.DataFrame([
        {"Strategie": info["name"], "beste Parameter": str(info["params"]),
         "Sharpe Standard": info["sharpe_is_default"], "Sharpe optimiert": info["sharpe_is"],
         "Plateau (Ø Nachbarn)": info["plateau_mean_sharpe"], "Nachbarn": info["plateau_n_neighbours"],
         "DSR": info["dsr"], "n_trials": info["n_trials"], "DSR alle Strategien": info["dsr_all_strategies"]}
        for info in best.values()
    ])
    st.dataframe(overview, width="stretch", hide_index=True)
    st.caption("Plateau: mittlere Sharpe Ratio der direkten Grid-Nachbarn der besten Kombination. "
               "DSR: Deflated Sharpe Ratio (Wahrscheinlichkeit einer echten Sharpe Ratio > 0 nach n_trials Versuchen).")

    names = {cls.name: cls.key for cls in STRATEGIES}
    choice = st.selectbox("Strategie", list(names))
    key = names[choice]
    heatmap = RESULTS_DIR / "optimization" / f"{key}_heatmap.png"
    if heatmap.exists():
        st.image(str(heatmap))
    results = read_csv_result(RESULTS_DIR / "optimization" / f"{key}.csv")
    if results is not None:
        st.subheader("Top 10 Kombinationen")
        st.dataframe(results.sort_values("sharpe", ascending=False).head(10).round(3), width="stretch", hide_index=True)


def page_regimes() -> None:
    """Seite «Marktphasen»: Kennzahlen pro Bull/Bear-Phase für alle Varianten (In-Sample)."""
    st.header("Marktphasen (In-Sample)")
    st.caption("Bull: Close(t−1) > SMA200(t−1), sonst Bear. Renditen der Phasentage werden verkettet.")
    summary = read_csv_result(RESULTS_DIR / "insample_summary.csv")
    if summary is None:
        return
    phases = summary[summary["scope"] != "gesamt"][
        ["variant", "scope", "share_days", "total_return", "sharpe", "max_drawdown"]]
    fig = px.bar(phases, x="variant", y="sharpe", color="scope", barmode="group",
                 color_discrete_map={"bull": "#2ea043", "bear": "#da3633"}, labels={"sharpe": "Sharpe Ratio"})
    fig.update_layout(height=450, xaxis_tickangle=-30)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(as_percent(phases.round(3)), width="stretch", hide_index=True)


def page_error_log() -> None:
    """Seite «KI-Fehlerlog»: gefundene Fehler im KI-Code mit Auswertung nach Kategorie."""
    st.header("KI-Fehlerlog")
    log = pd.read_csv(DOCS_DIR / "ki_fehlerlog.csv")
    if log.empty:
        st.info("Noch keine Einträge.")
        return
    col1, col2, col3 = st.columns(3)
    col1.subheader("Kategorie")
    col1.dataframe(log["kategorie"].value_counts())
    col2.subheader("Unterkategorie")
    col2.dataframe(log["unterkategorie"].value_counts())
    col3.subheader("Gefunden durch")
    col3.dataframe(log["gefunden_durch"].value_counts())
    st.dataframe(log, width="stretch", hide_index=True)


def main() -> None:
    """Navigation über die Seitenleiste."""
    st.set_page_config(page_title="BMA BTC Trading-Bot", layout="wide")
    settings = load_settings()
    page = st.sidebar.radio("Seite", PAGES)
    if page == "Daten":
        page_data(settings)
    elif page == "Strategien":
        page_strategies()
    elif page == "Optimierung":
        page_optimization()
    elif page == "Marktphasen":
        page_regimes()
    elif page == "KI-Fehlerlog":
        page_error_log()
    else:
        st.header(page)
        st.info("Der OOS-Test wird erst nach ausdrücklicher Freigabe durch das Team ausgeführt (scripts/run_oos.py).")


main()
