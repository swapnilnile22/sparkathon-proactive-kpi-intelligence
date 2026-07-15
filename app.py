"""Proactive KPI Intelligence — Sparkathon prototype (single-page app)."""
from __future__ import annotations

import streamlit as st

import config
import forecast_data as fd
import early_warning as ew
import investigation as inv
from ui.forecast_board import render_board
from ui.forecast_chart import render_chart
from ui.investigation_panel import render_stream

st.set_page_config(page_title="Proactive KPI Intelligence", layout="wide")

ref = fd.reference_date()


def _format_current(metric_key: str, value: float) -> str:
    if metric_key == "CSAT":
        return f"{value:.2f}"
    if metric_key == "AHT":
        return f"{value:.1f}"
    return f"{value:,.0f}"


# --- Header -----------------------------------------------------------------
st.title("Proactive KPI Intelligence")
st.caption(
    f"7-Day Early Warning · as of {ref.strftime('%A, %b %d, %Y')} · "
    "forecasts contact-center KPIs and investigates predicted anomalies "
    "before they impact customers."
)

# --- Compute forecasts + anomalies for every metric -------------------------
cards = []
anomalies: dict[str, ew.PredictedAnomaly] = {}
for m in config.METRICS:
    fc = fd.forecast(m.key, horizon=7)
    hist = fd.get_history(m.key)
    anomaly = ew.evaluate(m, fc, ref)
    if anomaly:
        anomalies[m.key] = anomaly
    cards.append(
        {
            "metric": m.display_name,
            "current": _format_current(m.key, hist[-1][1]),
            "target": f"{m.kpi_target:g}",
            "units": m.units,
            "forecast_values": [v for _, v in fc],
            "anomaly": anomaly,
        }
    )

# --- Forecast board ---------------------------------------------------------
st.subheader("7-Day Forecast Board")
st.caption("Each card shows the current value, target, and the 7-day forecast trend.")
clicked = render_board(cards)

# persist selection across reruns
if clicked:
    st.session_state["investigate"] = clicked

# --- Hero metric detail (first at-risk metric) ------------------------------
hero_key = next(iter(anomalies), None)
if hero_key:
    hero = config.metric_by_key(hero_key)
    hero_anom = anomalies[hero_key]
    st.subheader(f"Forecast detail — {hero.display_name}")
    render_chart(hero, fd.get_history(hero_key), fd.forecast(hero_key), hero_anom)

    st.error(
        f"**Early warning:** {hero.display_name} is forecast to fall below "
        f"target ({hero.kpi_target:g}{hero.units}) on "
        f"{hero_anom.first_breach_date.strftime('%A, %b %d')} — "
        f"{hero_anom.days_until} days out. Click **Investigate** on the card above."
    )

# --- Investigation ----------------------------------------------------------
target_key = st.session_state.get("investigate")
if target_key:
    metric = config.metric_by_key(target_key)
    anomaly = anomalies.get(target_key)
    if anomaly:
        st.subheader(f"Agentic Investigation — {metric.display_name}")
        st.caption(
            "An autonomous agent investigates the *predicted* anomaly across "
            "historical, correlated, and financial signals — before it happens."
        )
        render_stream(inv.stream_investigation(anomaly, metric, delay=0.8))
