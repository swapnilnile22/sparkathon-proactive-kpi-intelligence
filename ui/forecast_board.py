"""Renders the 7-day forecast board: one KPI card per metric."""
from __future__ import annotations

import streamlit as st


def _sparkline(values):
    # tiny inline sparkline via unicode blocks
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[int((v - lo) / span * (len(blocks) - 1))] for v in values)


def render_board(cards: list[dict]) -> str | None:
    clicked = None
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            anomaly = card["anomaly"]
            at_risk = anomaly is not None
            border = "#DC2626" if at_risk else "#16A34A"
            badge_bg = "#FEE2E2" if at_risk else "#DCFCE7"
            badge_fg = "#991B1B" if at_risk else "#166534"
            badge = (
                f"⚠️ At risk — breach in {anomaly.days_until}d"
                if at_risk
                else "✓ On track"
            )
            st.markdown(
                f"""
                <div style="border:2px solid {border};border-radius:12px;
                    padding:14px;background:#fff;">
                  <div style="font-size:0.8rem;color:#6B7280;">{card['metric']}</div>
                  <div style="font-size:1.6rem;font-weight:700;">
                      {card['current']}<span style="font-size:0.9rem;color:#6B7280;">
                      {card['units']}</span></div>
                  <div style="font-size:0.75rem;color:#6B7280;">
                      Target {card['target']}{card['units']}</div>
                  <div style="font-size:1.1rem;letter-spacing:1px;color:{border};">
                      {_sparkline(card['forecast_values'])}</div>
                  <div style="margin-top:8px;display:inline-block;padding:2px 8px;
                      border-radius:999px;background:{badge_bg};color:{badge_fg};
                      font-size:0.72rem;font-weight:600;">{badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if at_risk:
                if st.button("🔍 Investigate", key=f"inv_{card['metric']}"):
                    clicked = anomaly.metric_key
    return clicked
