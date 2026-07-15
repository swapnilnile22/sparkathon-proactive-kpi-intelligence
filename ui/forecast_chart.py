"""Plotly chart: recent history + 7-day forecast + target line + breach marker
(Command Center palette)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ui import style


def render_chart(metric, history, forecast_points, anomaly, key="forecast_chart"):
    hist_x = [d for d, _ in history]
    hist_y = [v for _, v in history]
    fc_x = [d for d, _ in forecast_points]
    fc_y = [v for _, v in forecast_points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hist_x, y=hist_y, name="Actual", mode="lines+markers",
            line=dict(color=style.HIST_LINE, width=2), marker=dict(size=6),
            hovertemplate="%{x|%a %b %d}<br>Actual: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[hist_x[-1]] + fc_x, y=[hist_y[-1]] + fc_y, name="Forecast",
            mode="lines+markers", line=dict(color=style.FC_LINE, width=2, dash="dash"),
            marker=dict(size=7),
            hovertemplate="%{x|%a %b %d}<br>Forecast: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=metric.kpi_target, line=dict(color=style.MUTED, dash="dot"),
        annotation_text=f"Target {metric.kpi_target:g}",
        annotation_position="top left",
        annotation_font=dict(color=style.MUTED, size=11),
    )

    if anomaly is not None:
        fig.add_vline(x=anomaly.first_breach_date, line=dict(color=style.BREACH, width=1))
        fig.add_trace(
            go.Scatter(
                x=[d for d, _ in anomaly.breach_days],
                y=[v for _, v in anomaly.breach_days],
                name="Predicted breach", mode="markers",
                marker=dict(color=style.BREACH, size=12, symbol="x"),
                hovertemplate="%{x|%a %b %d}<br>Breach: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=34, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="#fff", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Geist, sans-serif", color=style.TEXT, size=12),
        hoverlabel=dict(font_size=12, font_family="Geist, sans-serif"),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=style.GRID)
    fig.update_yaxes(showgrid=True, gridcolor=style.GRID, zeroline=False)

    return st.plotly_chart(
        fig, width="stretch", on_select="rerun", selection_mode="points", key=key,
    )
