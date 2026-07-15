"""Renders investigation layers as they stream in."""
from __future__ import annotations

import streamlit as st


def _render_layer(layer: dict) -> None:
    st.markdown(f"#### {layer['title']}")
    st.markdown(layer["content"])

    data = layer.get("data", {})
    if layer["name"] == "recommended_actions":
        for a in data.get("actions", []):
            st.markdown(
                f"**{a['priority']}. {a['action']}**  \n"
                f"<span style='color:#6B7280;font-size:0.85rem;'>"
                f"Impact: {a['impact']}</span>",
                unsafe_allow_html=True,
            )
    elif layer["name"] == "financial_impact":
        st.metric(
            "At-risk revenue (this week)",
            f"${data['at_risk_low_usd']:,}–${data['at_risk_high_usd']:,}",
        )
    elif layer["name"] == "probable_cause":
        st.metric("Confidence", f"{data['confidence_pct']}%")
        st.caption("Ruled out: " + ", ".join(data.get("ruled_out", [])))
    st.divider()


def render_stream(layer_iter) -> None:
    container = st.container()
    for layer in layer_iter:
        with container:
            _render_layer(layer)
