"""Agentic investigation of a *predicted* anomaly.

Primary path: a real Amazon Bedrock (Claude) Converse call produces the 7-layer
intelligence brief as JSON, which the app streams with a typing animation.
Fallback path: a hand-written synthetic brief, used automatically if Bedrock is
unavailable or errors (e.g. model access not yet enabled). All data in the
scenario is synthetic — no real customer, tenant, or user data.
"""
from __future__ import annotations

import json
import re
import time

import bedrock_client

LAYER_ORDER = [
    "predicted_brief",
    "historical_context",
    "correlated_signals",
    "probable_cause",
    "financial_impact",
    "normalization_forecast",
    "recommended_actions",
]


# --------------------------------------------------------------------------- #
# Prompt + parsing for the Bedrock path
# --------------------------------------------------------------------------- #
def _build_prompt(anomaly, metric) -> str:
    breach = anomaly.first_breach_date
    forecast_line = ", ".join(
        f"{d.strftime('%a %m-%d')}={v:.2f}" for d, v in anomaly.breach_days
    )
    return f"""You are an autonomous contact-center operations analyst. A forecasting
engine predicts that a KPI will breach its target in the next few days. Investigate this
PREDICTED (future, not-yet-occurred) anomaly and produce an early-warning intelligence brief.

SCENARIO (all synthetic demo data):
- Metric: {metric.display_name} ({metric.key}), units "{metric.units}"
- KPI target: {metric.kpi_target:g} ({metric.direction})
- Predicted first breach: {breach.strftime('%A, %b %d')} ({anomaly.days_until} days from now)
- Forecast values on breach days: {forecast_line}

Return ONLY a JSON object, no prose, no markdown fences, with this exact shape:
{{"layers": [
  {{"name":"predicted_brief","title":"Predicted Anomaly","content":"<markdown>","data":{{}}}},
  {{"name":"historical_context","title":"Historical Context","content":"<markdown>","data":{{}}}},
  {{"name":"correlated_signals","title":"Correlated Signals","content":"<markdown>","data":{{}}}},
  {{"name":"probable_cause","title":"Probable Cause","content":"<markdown>",
    "data":{{"confidence_pct":<int>,"ruled_out":["...","..."]}}}},
  {{"name":"financial_impact","title":"Projected Impact (if no action taken)","content":"<markdown>",
    "data":{{"at_risk_low_usd":<int>,"at_risk_high_usd":<int>}}}},
  {{"name":"normalization_forecast","title":"Normalization Forecast","content":"<markdown>","data":{{}}}},
  {{"name":"recommended_actions","title":"Recommended Pre-emptive Actions","content":"<markdown>",
    "data":{{"actions":[{{"priority":1,"action":"...","impact":"..."}}]}}}}
]}}

Rules:
- Layers MUST appear in exactly the order above with those exact "name" values.
- Frame everything as FUTURE / predicted ("is forecast to", "if no action is taken",
  "you have {anomaly.days_until} days to act"). The breach has NOT happened yet.
- recommended_actions must list 3 prioritised, PRE-EMPTIVE actions.
- Keep each content field to 1-3 sentences of operator-friendly markdown.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _validate_layers(obj: dict) -> list[dict]:
    layers = obj["layers"]
    names = [l["name"] for l in layers]
    if names != LAYER_ORDER:
        raise ValueError(f"unexpected layer names/order: {names}")
    for l in layers:
        if not l.get("title") or not l.get("content"):
            raise ValueError(f"layer {l.get('name')} missing title/content")
        l.setdefault("data", {})
    return layers


def generate_layers_bedrock(anomaly, metric) -> list[dict]:
    """Call Bedrock and return validated layers. Raises on any failure."""
    text = bedrock_client.converse_text(_build_prompt(anomaly, metric))
    return _validate_layers(_extract_json(text))


# --------------------------------------------------------------------------- #
# Synthetic fallback (used if Bedrock is unavailable)
# --------------------------------------------------------------------------- #
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
            "data": {"predicted_low": round(lowest, 2), "days_until": days},
        },
        {
            "name": "historical_context",
            "title": "Historical Context",
            "content": (
                "Over the last 90 days this pattern — a steady multi-day decline — has "
                "preceded a target miss **3 times**. In each case the dip lasted 4–6 days "
                "before recovering. The current trajectory most closely matches the "
                "incident 6 weeks ago."
            ),
            "data": {"similar_events": 3},
        },
        {
            "name": "correlated_signals",
            "title": "Correlated Signals",
            "content": (
                "Two related metrics are moving in the same window: **Average Handle Time "
                "is forecast to rise ~9%** and **transfer rate ~6%**. Rising handle time "
                "and transfers typically pull this metric down — a self-reinforcing pattern."
            ),
            "data": {"aht_change_pct": 9},
        },
        {
            "name": "probable_cause",
            "title": "Probable Cause",
            "content": (
                "**Most likely: an internal process/knowledge gap** (confidence **72%**). "
                "The correlated handle-time rise points to agents taking longer on a "
                "specific issue type, not to a volume surge or an external event."
            ),
            "data": {
                "confidence_pct": 72,
                "ruled_out": ["Seasonal", "Technical outage", "Volume surge"],
            },
        },
        {
            "name": "financial_impact",
            "title": "Projected Impact (if no action taken)",
            "content": (
                "If the forecast holds and no action is taken, the projected dip "
                "corresponds to an estimated **$18k–$34k** in at-risk revenue over the "
                "affected week. Acting before the breach avoids most of this."
            ),
            "data": {"at_risk_low_usd": 18000, "at_risk_high_usd": 34000},
        },
        {
            "name": "normalization_forecast",
            "title": "Normalization Forecast",
            "content": (
                f"Left unaddressed, the model expects the dip to persist ~5 days before "
                f"self-correcting. With a targeted intervention started now — {days} days "
                f"ahead — the breach can likely be prevented entirely."
            ),
            "data": {"expected_duration_days": 5},
        },
        {
            "name": "recommended_actions",
            "title": "Recommended Pre-emptive Actions",
            "content": "Prioritised actions to take **before** the predicted breach:",
            "data": {
                "actions": [
                    {
                        "priority": 1,
                        "action": "Push a targeted micro-coaching / knowledge update on the "
                        "top-driving issue type to the affected team.",
                        "impact": "Directly addresses the handle-time driver",
                    },
                    {
                        "priority": 2,
                        "action": "Add a temporary QA checkpoint on the correlated issue "
                        "type for the next 5 days.",
                        "impact": "Catches regressions early",
                    },
                    {
                        "priority": 3,
                        "action": "Brief team leads on the early warning and monitor the "
                        "metric daily through the risk window.",
                        "impact": "Fast course-correction if the trend worsens",
                    },
                ]
            },
        },
    ]


# --------------------------------------------------------------------------- #
# Streaming entry point
# --------------------------------------------------------------------------- #
def stream_investigation(anomaly, metric, delay: float = 0.6, use_bedrock: bool = True):
    """Yield the 7 layers one at a time. Uses Bedrock when available, else the
    synthetic fallback. `source` is attached to the first layer for the UI badge.
    """
    source = "fallback"
    if use_bedrock:
        try:
            layers = generate_layers_bedrock(anomaly, metric)
            source = "bedrock"
        except Exception:
            layers = build_layers(anomaly, metric)
    else:
        layers = build_layers(anomaly, metric)

    for i, layer in enumerate(layers):
        if i == 0:
            layer = {**layer, "source": source}
        yield layer
        if delay:
            time.sleep(delay)
