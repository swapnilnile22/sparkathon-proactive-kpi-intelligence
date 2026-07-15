"""Static metric definitions for the demo. Pure data, no logic."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    key: str
    display_name: str
    units: str
    kpi_target: float
    direction: str  # "higher_is_better" | "lower_is_better"
    baseline: float  # typical recent value used to build synthetic history


METRICS = [
    Metric("CSAT", "Customer Satisfaction", "/ 5", 4.0, "higher_is_better", 4.35),
    Metric("AHT", "Average Handle Time", "min", 8.0, "lower_is_better", 6.8),
    Metric("VOLUME", "Contact Volume", "calls/day", 5000.0, "lower_is_better", 3200.0),
    Metric("FCR", "First-Contact Resolution", "%", 75.0, "higher_is_better", 82.0),
]

_BY_KEY = {m.key: m for m in METRICS}


def metric_by_key(key: str) -> Metric:
    return _BY_KEY[key]
