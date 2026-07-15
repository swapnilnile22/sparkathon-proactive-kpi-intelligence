"""Proactive KPI Intelligence — Sparkathon prototype (single-page app)."""
from __future__ import annotations

import os

import streamlit as st

import config
import forecast_data as fd
import early_warning as ew
import investigation as inv
from ui import style
from ui.forecast_board import render_board
from ui.forecast_chart import render_chart
from ui.investigation_panel import render_stream

st.set_page_config(page_title="Proactive KPI Intelligence", layout="wide")
style.inject()

ref = fd.reference_date()


def _format_current(metric_key: str, value: float) -> str:
    if metric_key == "CSAT":
        return f"{value:.2f}"
    if metric_key == "AHT":
        return f"{value:.1f}"
    return f"{value:,.0f}"


# --- Header -----------------------------------------------------------------
st.markdown(
    f"""
    <div class="pki-title">Proactive KPI Intelligence</div>
    <div class="pki-sub">7-Day Early Warning · as of {ref.strftime('%A, %b %d, %Y')} ·
    forecasts contact-center KPIs and investigates predicted anomalies before they
    impact customers.</div>
    """,
    unsafe_allow_html=True,
)

# --- Load forecasts (from the DynamoDB forecast cache when configured) -------
ddb_forecasts: dict[str, list] = {}
data_source = "computed locally (synthetic)"
if os.environ.get("DDB_TABLE"):
    try:
        import ddb_store

        tenant_id = ddb_store.TENANTS[0]  # single demo tenant, no picker
        ddb_forecasts = ddb_store.read_forecasts(tenant_id)
        if ddb_forecasts:
            data_source = "DynamoDB forecast cache (us-east-1)"
    except Exception:
        ddb_forecasts = {}
st.caption(f"Forecast source: {data_source}")

# --- Compute forecasts + anomalies for every metric -------------------------
cards = []
anomalies: dict[str, ew.PredictedAnomaly] = {}
forecasts: dict[str, list] = {}
for m in config.METRICS:
    fc = ddb_forecasts.get(m.key) or fd.forecast(m.key, horizon=7)
    forecasts[m.key] = fc
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

# --- Investigation popup ----------------------------------------------------
@st.dialog("🔎 Agentic Investigation", width="large")
def _investigation_dialog(metric_key: str) -> None:
    metric = config.metric_by_key(metric_key)
    anomaly = anomalies.get(metric_key)
    focus = st.session_state.get("focus")
    subtitle = metric.display_name
    if focus:
        subtitle += f" · selected {focus['label']}"
    st.markdown(f"### {subtitle}")
    st.caption(
        "An autonomous agent analyses this metric's 7-day forecast across "
        "historical, correlated, and financial signals."
    )
    render_stream(
        inv.stream_investigation(
            metric, forecasts[metric_key], anomaly=anomaly, focus=focus, delay=0.6
        )
    )


# --- Forecast board ---------------------------------------------------------
st.subheader("7-Day Forecast Board")
st.caption("Each card shows the current value, target, and the 7-day forecast trend.")
render_board(cards)

# --- Metric chart (any metric selectable) -----------------------------------
metric_keys = [m.key for m in config.METRICS]
hero_key = next(iter(anomalies), metric_keys[0])
sel_key = st.radio(
    "View forecast for metric",
    metric_keys,
    index=metric_keys.index(hero_key),
    format_func=lambda k: config.metric_by_key(k).display_name,
    horizontal=True,
)
sel = config.metric_by_key(sel_key)
sel_anom = anomalies.get(sel_key)

st.subheader(f"Forecast detail — {sel.display_name}")
if sel_anom:
    st.error(
        f"**Early warning:** {sel.display_name} is forecast to fall below "
        f"target ({sel.kpi_target:g}{sel.units}) on "
        f"{sel_anom.first_breach_date.strftime('%A, %b %d')} — "
        f"{sel_anom.days_until} days out."
    )
else:
    st.success(
        f"{sel.display_name} is on track — the forecast stays within target all week."
    )
st.caption("💡 Click any point on the forecast line to investigate that day.")

event = render_chart(
    sel, fd.get_history(sel_key), forecasts[sel_key], sel_anom, key=f"chart_{sel_key}",
)

# detect a clicked point on ANY metric; capture WHICH point for the popup
selection = getattr(event, "selection", None)
points = (
    selection.get("points", [])
    if isinstance(selection, dict)
    else getattr(selection, "points", [])
)
if points:
    p = points[0]
    label = str(p.get("x", ""))
    try:
        value = float(p.get("y"))
    except (TypeError, ValueError):
        value = None
    sel_id = f"{sel_key}:{label}"
    if st.session_state.get("last_sel") != sel_id:
        st.session_state["last_sel"] = sel_id
        st.session_state["focus"] = (
            {"label": label, "value": value} if value is not None else None
        )
        st.session_state["open_inv"] = sel_key

# --- Open the popup if a trigger fired this run -----------------------------
if st.session_state.get("open_inv"):
    _investigation_dialog(st.session_state.pop("open_inv"))
