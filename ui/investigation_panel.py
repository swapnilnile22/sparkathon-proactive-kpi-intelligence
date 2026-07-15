"""Renders investigation layers as they stream in (Command Center AI-panel style).

Defensive: layer content may come from a live Bedrock model, so every data
lookup uses .get() with fallbacks.
"""
from __future__ import annotations

import streamlit as st

from ui import style


def _render_layer(layer: dict) -> None:
    if layer.get("source"):
        badge = "⚡ Live Bedrock agent" if layer["source"] == "bedrock" else "Demo brief (offline)"
        st.caption(f"Investigation source: {badge}")

    data = layer.get("data") or {}
    name = layer.get("name")

    # Build the inner HTML for the gradient panel
    body = (
        f"<div class='pki-layer-title'>{layer.get('title','Layer')}</div>"
        f"<div style='color:{style.TEXT};font-size:0.92rem;'>{_md_to_html(layer.get('content',''))}</div>"
    )
    st.markdown(
        f"<div class='pki-panel-wrap'><div class='pki-panel'>{body}</div></div>",
        unsafe_allow_html=True,
    )

    # Structured extras below the panel
    if name == "recommended_actions":
        for a in data.get("actions", []):
            st.markdown(
                f"<div class='pki-action'><b>{a.get('priority','•')}. "
                f"{a.get('action','')}</b><br>"
                f"<span class='imp'>Impact: {a.get('impact','')}</span></div>",
                unsafe_allow_html=True,
            )
    elif name == "financial_impact":
        lo, hi = data.get("at_risk_low_usd"), data.get("at_risk_high_usd")
        if lo is not None and hi is not None:
            st.markdown(
                f"<span class='pki-pill'>At-risk revenue this week: "
                f"${lo:,}–${hi:,}</span>",
                unsafe_allow_html=True,
            )
    elif name == "probable_cause":
        bits = []
        if data.get("confidence_pct") is not None:
            bits.append(f"Confidence {data['confidence_pct']}%")
        if data.get("ruled_out"):
            bits.append("Ruled out: " + ", ".join(data["ruled_out"]))
        if bits:
            st.markdown(
                f"<span class='pki-pill'>{' · '.join(bits)}</span>",
                unsafe_allow_html=True,
            )


def _md_to_html(text: str) -> str:
    # minimal **bold** support for the panel body
    import re

    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def render_stream(layer_iter) -> None:
    container = st.container()
    for layer in layer_iter:
        with container:
            _render_layer(layer)
