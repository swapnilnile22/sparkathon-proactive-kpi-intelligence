"""Renders the 7-day forecast board: one KPI card per metric (Command Center style)."""
from __future__ import annotations

import streamlit as st

from ui import style


def _sparkline(values):
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[int((v - lo) / span * (len(blocks) - 1))] for v in values)


def render_board(cards: list[dict]) -> None:
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            anomaly = card["anomaly"]
            at_risk = anomaly is not None
            spark_color = style.BREACH if at_risk else style.OK_FG
            badge_cls = "risk" if at_risk else "ok"
            badge = (
                f"⚠️ At risk · breach in {anomaly.days_until}d"
                if at_risk
                else "✓ On track"
            )
            st.markdown(
                f"""
                <div class="pki-card {'risk' if at_risk else ''}">
                  <div class="pki-name">{card['metric']}</div>
                  <div class="pki-value">{card['current']}
                    <span class="pki-unit">{card['units']}</span></div>
                  <div class="pki-target">Target {card['target']}{card['units']}</div>
                  <div class="pki-spark" style="color:{spark_color};">
                    {_sparkline(card['forecast_values'])}</div>
                  <div class="pki-badge {badge_cls}">{badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
