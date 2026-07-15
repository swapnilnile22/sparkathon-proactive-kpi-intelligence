"""Agentic investigation of a forecast point / predicted anomaly.

Works for ANY metric: if the metric is at-risk (a predicted breach) it produces
an early-warning brief with pre-emptive actions; if it's on-track it produces a
stability brief with light monitoring actions. Primary path is a real Amazon
Bedrock (Claude) Converse call returning the 7 layers as JSON; a hand-written
synthetic brief is the automatic fallback. All data is synthetic.
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

# Titles differ by case (at-risk vs on-track); layer NAMES stay constant.
_TITLES = {
    True: {
        "predicted_brief": "Predicted Anomaly",
        "historical_context": "Historical Context",
        "correlated_signals": "Correlated Signals",
        "probable_cause": "Probable Cause",
        "financial_impact": "Projected Impact (if no action taken)",
        "normalization_forecast": "Normalization Forecast",
        "recommended_actions": "Recommended Pre-emptive Actions",
    },
    False: {
        "predicted_brief": "Forecast Summary",
        "historical_context": "Historical Context",
        "correlated_signals": "Correlated Signals",
        "probable_cause": "Stability Assessment",
        "financial_impact": "Financial Outlook",
        "normalization_forecast": "Trajectory",
        "recommended_actions": "Recommended Monitoring",
    },
}


def _focus_line(focus) -> str:
    if not focus:
        return ""
    return (
        f"\n- OPERATOR SELECTED the forecast point for {focus['label']} "
        f"(forecast value {focus['value']:.2f}). Open the first layer by naming THIS "
        f"specific day and value, then analyse the trajectory around it."
    )


# --------------------------------------------------------------------------- #
# Bedrock path
# --------------------------------------------------------------------------- #
def _build_prompt(metric, forecast_points, anomaly, focus=None) -> str:
    at_risk = anomaly is not None
    titles = _TITLES[at_risk]
    fdates = ", ".join(f"{d.strftime('%a %m-%d')}={v:.2f}" for d, v in forecast_points)

    if at_risk:
        situation = (
            f"is PREDICTED TO BREACH its target ({metric.kpi_target:g}) on "
            f"{anomaly.first_breach_date.strftime('%A, %b %d')} "
            f"({anomaly.days_until} days from now)."
        )
        guidance = (
            "Frame everything as FUTURE / predicted early warning. "
            "recommended_actions must list 3 prioritised PRE-EMPTIVE actions."
        )
    else:
        situation = (
            f"is ON TRACK — the 7-day forecast stays within target "
            f"({metric.kpi_target:g}, {metric.direction}). No breach is predicted."
        )
        guidance = (
            "Confirm the healthy trajectory and WHY. Do NOT invent a breach or risk. "
            "The financial layer should state there is no material risk this week. "
            "recommended_actions must list 3 light MONITORING actions."
        )

    layer_schema = ",\n  ".join(
        f'{{"name":"{n}","title":"{titles[n]}","content":"<markdown, 1-3 sentences>","data":{{}}}}'
        if n not in ("probable_cause", "financial_impact", "recommended_actions")
        else {
            "probable_cause": f'{{"name":"probable_cause","title":"{titles["probable_cause"]}","content":"<markdown>","data":{{"confidence_pct":<int>,"ruled_out":["...","..."]}}}}',
            "financial_impact": f'{{"name":"financial_impact","title":"{titles["financial_impact"]}","content":"<markdown>","data":{{"at_risk_low_usd":<int>,"at_risk_high_usd":<int>}}}}',
            "recommended_actions": f'{{"name":"recommended_actions","title":"{titles["recommended_actions"]}","content":"<markdown>","data":{{"actions":[{{"priority":1,"action":"...","impact":"..."}}]}}}}',
        }[n]
        for n in LAYER_ORDER
    )

    return f"""You are an autonomous contact-center operations analyst. A forecasting engine
has produced a 7-day forecast for a KPI. Investigate it and produce an intelligence brief.

SCENARIO (all synthetic demo data):
- Metric: {metric.display_name} ({metric.key}), units "{metric.units}"
- KPI target: {metric.kpi_target:g} ({metric.direction})
- This metric {situation}
- 7-day forecast: {fdates}{_focus_line(focus)}

{guidance}

Return ONLY a JSON object, no prose, no markdown fences, with this exact shape:
{{"layers": [
  {layer_schema}
]}}

Rules:
- Layers MUST appear in exactly this order with those exact "name" values and titles.
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


def generate_layers_bedrock(metric, forecast_points, anomaly=None, focus=None) -> list[dict]:
    text = bedrock_client.converse_text(_build_prompt(metric, forecast_points, anomaly, focus))
    return _validate_layers(_extract_json(text))


# --------------------------------------------------------------------------- #
# Synthetic fallback
# --------------------------------------------------------------------------- #
def build_layers(metric, forecast_points, anomaly=None, focus=None) -> list[dict]:
    at_risk = anomaly is not None
    titles = _TITLES[at_risk]
    values = [v for _, v in forecast_points]
    lo, hi = min(values), max(values)

    focus_prefix = ""
    if focus:
        focus_prefix = (
            f"**Selected point — {focus['label']}: {focus['value']:.2f}{metric.units}.** "
        )

    if at_risk:
        breach_str = anomaly.first_breach_date.strftime("%A, %b %d")
        days = anomaly.days_until
        lowest = min(v for _, v in anomaly.breach_days)
        return [
            {"name": "predicted_brief", "title": titles["predicted_brief"], "content": (
                f"{focus_prefix}**{metric.display_name} is forecast to fall below target "
                f"({metric.kpi_target:g}{metric.units}) on {breach_str}** — {days} days from now. "
                f"Projected low of **{lowest:.2f}**. No breach has occurred yet; this is an early "
                "warning with time to act."), "data": {"days_until": days}},
            {"name": "historical_context", "title": titles["historical_context"], "content": (
                "Over the last 90 days this pattern — a steady multi-day decline — has preceded a "
                "target miss **3 times**, each lasting 4–6 days before recovering. The current "
                "trajectory most closely matches the incident 6 weeks ago."), "data": {}},
            {"name": "correlated_signals", "title": titles["correlated_signals"], "content": (
                "**Average Handle Time is forecast to rise ~9%** and **transfer rate ~6%** in the "
                "same window — both typically pull this metric down, a self-reinforcing pattern."),
                "data": {}},
            {"name": "probable_cause", "title": titles["probable_cause"], "content": (
                "**Most likely: an internal process/knowledge gap** (confidence **72%**). The "
                "correlated handle-time rise points to agents taking longer on a specific issue "
                "type, not a volume surge or external event."),
                "data": {"confidence_pct": 72, "ruled_out": ["Seasonal", "Technical outage", "Volume surge"]}},
            {"name": "financial_impact", "title": titles["financial_impact"], "content": (
                "If the forecast holds and no action is taken, the projected dip corresponds to an "
                "estimated **$18k–$34k** in at-risk revenue over the affected week. Acting before "
                "the breach avoids most of this."),
                "data": {"at_risk_low_usd": 18000, "at_risk_high_usd": 34000}},
            {"name": "normalization_forecast", "title": titles["normalization_forecast"], "content": (
                f"Left unaddressed, the dip is expected to persist ~5 days before self-correcting. "
                f"With a targeted intervention started now — {days} days ahead — the breach can "
                "likely be prevented entirely."), "data": {}},
            {"name": "recommended_actions", "title": titles["recommended_actions"], "content":
                "Prioritised actions to take **before** the predicted breach:", "data": {"actions": [
                    {"priority": 1, "action": "Push targeted micro-coaching / a knowledge update on the top-driving issue type to the affected team.", "impact": "Directly addresses the handle-time driver"},
                    {"priority": 2, "action": "Add a temporary QA checkpoint on the correlated issue type for the next 5 days.", "impact": "Catches regressions early"},
                    {"priority": 3, "action": "Brief team leads on the early warning and monitor the metric daily through the risk window.", "impact": "Fast course-correction if the trend worsens"},
                ]}},
        ]

    # On-track brief
    return [
        {"name": "predicted_brief", "title": titles["predicted_brief"], "content": (
            f"{focus_prefix}**{metric.display_name} is on track.** The 7-day forecast stays within "
            f"target ({metric.kpi_target:g}{metric.units}), ranging **{lo:.2f}–{hi:.2f}**. No breach "
            "is predicted this week."), "data": {}},
        {"name": "historical_context", "title": titles["historical_context"], "content": (
            "This metric has held steady over the last 90 days; the current forecast is consistent "
            "with its healthy baseline and shows no unusual deviation."), "data": {}},
        {"name": "correlated_signals", "title": titles["correlated_signals"], "content": (
            "No correlated metrics are trending adversely in this window — the drivers that usually "
            "move this KPI are all stable."), "data": {}},
        {"name": "probable_cause", "title": titles["probable_cause"], "content": (
            "**Stable — no cause for concern** (confidence **90%**). Forecast variance is within "
            "normal day-to-day range."), "data": {"confidence_pct": 90, "ruled_out": []}},
        {"name": "financial_impact", "title": titles["financial_impact"], "content": (
            "**No material financial risk** attributable to this metric this week."), "data": {}},
        {"name": "normalization_forecast", "title": titles["normalization_forecast"], "content": (
            "Flat, healthy trajectory expected to continue through the forecast window."), "data": {}},
        {"name": "recommended_actions", "title": titles["recommended_actions"], "content":
            "Light monitoring only — no intervention needed:", "data": {"actions": [
                {"priority": 1, "action": "Keep this metric on the standard daily review.", "impact": "Early detection if the trend changes"},
                {"priority": 2, "action": "No staffing or process change required.", "impact": "Avoids unnecessary churn"},
                {"priority": 3, "action": "Re-check after the next forecast refresh.", "impact": "Confirms continued stability"},
            ]}},
    ]


# --------------------------------------------------------------------------- #
# Streaming entry point
# --------------------------------------------------------------------------- #
def stream_investigation(
    metric, forecast_points, anomaly=None, focus=None, delay: float = 0.6, use_bedrock: bool = True
):
    """Yield the 7 layers one at a time for any metric (at-risk or on-track)."""
    source = "fallback"
    if use_bedrock:
        try:
            layers = generate_layers_bedrock(metric, forecast_points, anomaly, focus)
            source = "bedrock"
        except Exception:
            layers = build_layers(metric, forecast_points, anomaly, focus)
    else:
        layers = build_layers(metric, forecast_points, anomaly, focus)

    for i, layer in enumerate(layers):
        if i == 0:
            layer = {**layer, "source": source}
        yield layer
        if delay:
            time.sleep(delay)
