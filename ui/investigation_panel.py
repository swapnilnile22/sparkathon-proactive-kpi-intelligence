"""Renders investigation layers as they stream in.

Defensive by design: the layer content may come from a live Bedrock model, so
every data lookup uses .get() with fallbacks rather than hard indexing.
"""
from __future__ import annotations

import streamlit as st


def _render_layer(layer: dict) -> None:
    if layer.get("source"):
        badge = "⚡ Live Bedrock agent" if layer["source"] == "bedrock" else "Demo brief"
        st.caption(f"Investigation source: {badge}")

    st.markdown(f"#### {layer.get('title', 'Layer')}")
    st.markdown(layer.get("content", ""))

    data = layer.get("data") or {}
    name = layer.get("name")

    if name == "recommended_actions":
        for a in data.get("actions", []):
            st.markdown(
                f"**{a.get('priority', '•')}. {a.get('action', '')}**  \n"
                f"<span style='color:#6B7280;font-size:0.85rem;'>"
                f"Impact: {a.get('impact', '')}</span>",
                unsafe_allow_html=True,
            )
    elif name == "financial_impact":
        lo = data.get("at_risk_low_usd")
        hi = data.get("at_risk_high_usd")
        if lo is not None and hi is not None:
            st.metric("At-risk revenue (this week)", f"${lo:,}–${hi:,}")
    elif name == "probable_cause":
        if data.get("confidence_pct") is not None:
            st.metric("Confidence", f"{data['confidence_pct']}%")
        if data.get("ruled_out"):
            st.caption("Ruled out: " + ", ".join(data["ruled_out"]))
    st.divider()


def render_stream(layer_iter) -> None:
    container = st.container()
    for layer in layer_iter:
        with container:
            _render_layer(layer)
