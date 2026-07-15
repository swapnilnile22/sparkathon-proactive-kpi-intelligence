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
tenant_id = None
if os.environ.get("DDB_TABLE"):
    try:
        import ddb_store

        tenant_id = st.sidebar.selectbox("Tenant", ddb_store.TENANTS)
        ddb_forecasts = ddb_store.read_forecasts(tenant_id)
        if ddb_forecasts:
            data_source = f"DynamoDB forecast cache · tenant {tenant_id[:8]}…"
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
    if not anomaly:
        st.info("No predicted anomaly for this metric.")
        return
    focus = st.session_state.get("focus")
    subtitle = metric.display_name
    if focus:
        subtitle += f" · selected {focus['label']}"
    st.markdown(f"### {subtitle}")
    st.caption(
        "An autonomous agent investigates the *predicted* anomaly across "
        "historical, correlated, and financial signals — before it happens."
    )
    render_stream(inv.stream_investigation(anomaly, metric, delay=0.6, focus=focus))


# --- Forecast board ---------------------------------------------------------
st.subheader("7-Day Forecast Board")
st.caption("Each card shows the current value, target, and the 7-day forecast trend.")
clicked = render_board(cards)
if clicked:
    st.session_state["focus"] = None  # card button → whole-anomaly view
    st.session_state["open_inv"] = clicked

# --- Hero metric detail (first at-risk metric) ------------------------------
hero_key = next(iter(anomalies), None)
if hero_key:
    hero = config.metric_by_key(hero_key)
    hero_anom = anomalies[hero_key]
    st.subheader(f"Forecast detail — {hero.display_name}")

    st.error(
        f"**Early warning:** {hero.display_name} is forecast to fall below "
        f"target ({hero.kpi_target:g}{hero.units}) on "
        f"{hero_anom.first_breach_date.strftime('%A, %b %d')} — "
        f"{hero_anom.days_until} days out."
    )
    st.caption("💡 Click any point on the forecast line — or the card button — to investigate.")

    event = render_chart(
        hero, fd.get_history(hero_key), forecasts[hero_key],
        hero_anom, key=f"chart_{hero_key}",
    )

    # detect a clicked point; capture WHICH point so the popup is specific to it
    sel = getattr(event, "selection", None)
    points = sel.get("points", []) if isinstance(sel, dict) else getattr(sel, "points", [])
    if points:
        p = points[0]
        label = str(p.get("x", ""))
        try:
            value = float(p.get("y"))
        except (TypeError, ValueError):
            value = None
        sel_id = f"{hero_key}:{label}"
        if st.session_state.get("last_sel") != sel_id:
            st.session_state["last_sel"] = sel_id
            st.session_state["focus"] = {"label": label, "value": value} if value is not None else None
            st.session_state["open_inv"] = hero_key

# --- Open the popup if a trigger fired this run -----------------------------
if st.session_state.get("open_inv"):
    _investigation_dialog(st.session_state.pop("open_inv"))
