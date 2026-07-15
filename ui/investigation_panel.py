"""Renders investigation layers as they stream in (Command Center AI-panel style).

Everything for a layer is rendered inside one gradient panel. Dollar signs are
HTML-escaped so Streamlit's KaTeX doesn't mangle currency figures. Defensive:
content may come from a live Bedrock model, so lookups use .get().
"""
from __future__ import annotations

import re

import streamlit as st

from ui import style


def _html(text: str) -> str:
    """Escape $ (avoid KaTeX) and convert **bold** to <b>."""
    text = (text or "").replace("$", "&#36;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _extras_html(layer: dict) -> str:
    data = layer.get("data") or {}
    name = layer.get("name")

    if name == "recommended_actions":
        items = ""
        for a in data.get("actions", []):
            items += (
                f"<div class='pki-action'><b>{a.get('priority','•')}. "
                f"{_html(a.get('action',''))}</b><br>"
                f"<span class='imp'>Impact: {_html(a.get('impact',''))}</span></div>"
            )
        return items

    if name == "probable_cause":
        bits = []
        if data.get("confidence_pct") is not None:
            bits.append(f"Confidence {data['confidence_pct']}%")
        if data.get("ruled_out"):
            bits.append("Ruled out: " + ", ".join(data["ruled_out"]))
        if bits:
            return f"<div class='pki-pill'>{' · '.join(bits)}</div>"
    return ""


def _render_layer(layer: dict) -> None:
    if layer.get("source") == "bedrock":
        st.caption("⚡ Live Bedrock agent")

    body = (
        f"<div class='pki-layer-title'>{layer.get('title','Layer')}</div>"
        f"<div style='color:{style.TEXT};font-size:0.92rem;line-height:1.5;'>"
        f"{_html(layer.get('content',''))}</div>"
        f"{_extras_html(layer)}"
    )
    st.markdown(
        f"<div class='pki-panel-wrap'><div class='pki-panel'>{body}</div></div>",
        unsafe_allow_html=True,
    )


def render_stream(layer_iter) -> None:
    container = st.container()
    for layer in layer_iter:
        with container:
            _render_layer(layer)
