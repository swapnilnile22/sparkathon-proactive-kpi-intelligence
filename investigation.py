"""Hand-written synthetic agentic investigation for the CSAT scenario.

All narrative is invented for this demo. It intentionally does NOT reproduce
any real prompt, taxonomy, or model output. Framing is future/predictive.
"""
from __future__ import annotations

import time

LAYER_ORDER = [
    "predicted_brief",
    "historical_context",
    "correlated_signals",
    "probable_cause",
    "financial_impact",
    "normalization_forecast",
    "recommended_actions",
]


def build_layers(anomaly, metric) -> list[dict]:
    breach = anomaly.first_breach_date
    breach_str = breach.strftime("%A, %b %d")
    days = anomaly.days_until
    lowest = min(v for _, v in anomaly.breach_days)

    return [
        {
            "name": "predicted_brief",
            "title": "Predicted Anomaly",
            "content": (
                f"**{metric.display_name} is forecast to fall below target "
                f"({metric.kpi_target:g}{metric.units}) on {breach_str}** — "
                f"{days} days from now. Projected low of **{lowest:.2f}**. "
                "No breach has occurred yet; this is an early warning with time to act."
            ),
            "data": {
                "metric": metric.display_name,
                "target": metric.kpi_target,
                "predicted_low": round(lowest, 2),
                "breach_date": breach_str,
                "days_until": days,
            },
        },
        {
            "name": "historical_context",
            "title": "Historical Context",
            "content": (
                "Over the last 90 days this pattern — a steady multi-day CSAT "
                "decline — has preceded a target miss **3 times**. In each case the "
                "dip lasted 4–6 days before recovering. The current trajectory most "
                "closely matches the incident 6 weeks ago."
            ),
            "data": {"similar_events": 3, "typical_duration_days": "4-6"},
        },
        {
            "name": "correlated_signals",
            "title": "Correlated Signals",
            "content": (
                "Two related metrics are moving in the same window: **Average "
                "Handle Time is forecast to rise ~9%** and **transfer rate ~6%**. "
                "Rising handle time and transfers typically pull CSAT down — a "
                "consistent, self-reinforcing pattern."
            ),
            "data": {"aht_change_pct": 9, "transfer_rate_change_pct": 6},
        },
        {
            "name": "probable_cause",
            "title": "Probable Cause",
            "content": (
                "**Most likely: an internal process/knowledge gap** (confidence "
                "**72%**). The correlated handle-time rise points to agents taking "
                "longer to resolve a specific issue type, not to a volume surge or "
                "an external event. Ruled out: seasonal effect, technical outage."
            ),
            "data": {
                "classification": "Internal process / knowledge gap",
                "confidence_pct": 72,
                "ruled_out": ["Seasonal", "Technical outage", "Volume surge"],
            },
        },
        {
            "name": "financial_impact",
            "title": "Projected Impact (if no action taken)",
            "content": (
                "If the forecast holds and no action is taken, the projected "
                "CSAT dip corresponds to an estimated **$18k–$34k** in at-risk "
                "revenue over the affected week (churn-risk + retention-offer "
                "modelling). Acting before the breach avoids most of this."
            ),
            "data": {"at_risk_low_usd": 18000, "at_risk_high_usd": 34000},
        },
        {
            "name": "normalization_forecast",
            "title": "Normalization Forecast",
            "content": (
                f"Left unaddressed, the model expects the dip to persist ~5 days "
                f"before self-correcting. With a targeted intervention started now "
                f"— {days} days ahead — the breach can likely be prevented entirely."
            ),
            "data": {"expected_duration_days": 5, "preventable": True},
        },
        {
            "name": "recommended_actions",
            "title": "Recommended Pre-emptive Actions",
            "content": "Prioritised actions to take **before** the predicted breach:",
            "data": {
                "actions": [
                    {
                        "priority": 1,
                        "action": "Push a targeted micro-coaching / knowledge "
                        "update on the top-driving issue type to the affected team.",
                        "impact": "Directly addresses the handle-time driver",
                    },
                    {
                        "priority": 2,
                        "action": "Add a temporary QA checkpoint on the correlated "
                        "issue type for the next 5 days.",
                        "impact": "Catches regressions early",
                    },
                    {
                        "priority": 3,
                        "action": "Brief team leads on the early warning and monitor "
                        "CSAT daily through the risk window.",
                        "impact": "Fast course-correction if the trend worsens",
                    },
                ]
            },
        },
    ]


def stream_investigation(anomaly, metric, delay: float = 0.9):
    for layer in build_layers(anomaly, metric):
        yield layer
        if delay:
            time.sleep(delay)
