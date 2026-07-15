"""Turns a forecast into a predicted KPI-target breach. The 'missing brain':
compare each forecast day to the KPI target, respecting metric direction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from config import Metric


@dataclass
class PredictedAnomaly:
    metric_key: str
    first_breach_date: date
    days_until: int
    severity: float  # |value - target| / target at the first breach
    breach_days: list  # list[tuple[date, float]]


def _breaches(value: float, target: float, direction: str) -> bool:
    if direction == "higher_is_better":
        return value < target
    return value > target


def evaluate(metric: Metric, forecast_points, reference: date):
    breaches = [
        (d, v)
        for d, v in forecast_points
        if _breaches(v, metric.kpi_target, metric.direction)
    ]
    if not breaches:
        return None

    first_date, first_val = breaches[0]
    days_until = (first_date - reference).days
    severity = abs(first_val - metric.kpi_target) / metric.kpi_target
    return PredictedAnomaly(
        metric_key=metric.key,
        first_breach_date=first_date,
        days_until=days_until,
        severity=round(severity, 4),
        breach_days=breaches,
    )
