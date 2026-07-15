"""Plotly chart: recent history + 7-day forecast + target line + breach marker."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_chart(metric, history, forecast_points, anomaly) -> None:
    hist_x = [d for d, _ in history]
    hist_y = [v for _, v in history]
    fc_x = [d for d, _ in forecast_points]
    fc_y = [v for _, v in forecast_points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=hist_x, y=hist_y, name="Actual (history)",
                   mode="lines+markers", line=dict(color="#111827"))
    )
    fig.add_trace(
        go.Scatter(x=[hist_x[-1]] + fc_x, y=[hist_y[-1]] + fc_y,
                   name="Forecast (next 7 days)", mode="lines+markers",
                   line=dict(color="#0B5FFF", dash="dash"))
    )
    fig.add_hline(y=metric.kpi_target, line=dict(color="#6B7280", dash="dot"),
                  annotation_text=f"Target {metric.kpi_target:g}",
                  annotation_position="top left")

    if anomaly is not None:
        fig.add_vline(x=anomaly.first_breach_date, line=dict(color="#DC2626"))
        fig.add_trace(
            go.Scatter(
                x=[d for d, _ in anomaly.breach_days],
                y=[v for _, v in anomaly.breach_days],
                name="Predicted breach", mode="markers",
                marker=dict(color="#DC2626", size=11, symbol="x"),
            )
        )

    fig.update_layout(
        height=360, margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="#fff",
    )
    st.plotly_chart(fig, use_container_width=True)
