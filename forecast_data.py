"""Deterministic synthetic history + genuinely computed 7-day forecasts.

History is fixed (seeded) so every page load is identical. The forecast is
computed live with Holt-Winters (statsmodels); if statsmodels is unavailable
or errors, a linear-trend fallback is used. This is public-domain time-series
math, not proprietary methodology.
"""
from __future__ import annotations

import math
import os
from datetime import date, timedelta

from config import metric_by_key

# Fixed anchor so the demo is fully deterministic. Labelled as the demo's
# "today"; the CSAT breach lands ~3 days out. Forecast covers the next 7 days.
_REFERENCE = date(2026, 7, 16)


def reference_date() -> date:
    return _REFERENCE


def _seed_from(seed_str: str) -> int:
    # stable, process-independent seed (Python's built-in hash() is salted)
    return sum((i + 1) * ord(c) for i, c in enumerate(seed_str))


def _seeded_noise(seed_str: str, n: int) -> list[float]:
    """Small deterministic pseudo-noise in roughly [-1, 1], no RNG state."""
    base = _seed_from(seed_str)
    return [math.sin(base * 0.013 + i * 1.7) for i in range(n)]


def get_history(metric_key: str, days: int = 14) -> list[tuple[date, float]]:
    """Return synthetic KPI history (the chart's actual-line). The forecast
    cache in DynamoDB holds forward-dated forecasts, not actuals — those are
    read separately via ddb_store.read_forecasts()."""
    return _synthetic_history(metric_key, days)


def _synthetic_history(metric_key: str, days: int = 14) -> list[tuple[date, float]]:
    m = metric_by_key(metric_key)
    start = _REFERENCE - timedelta(days=days)
    noise = _seeded_noise(metric_key, days)

    points: list[tuple[date, float]] = []
    for i in range(days):
        d = start + timedelta(days=i)
        base = m.baseline
        if metric_key == "CSAT":
            # steady two-week decline (4.66 -> ~4.14); Holt-Winters projects the
            # trend to cross the 4.0 target ~3 days into the forecast horizon.
            val = 4.66 - 0.04 * i + 0.02 * noise[i]
        elif metric_key == "AHT":
            val = base + 0.15 * noise[i]
        elif metric_key == "VOLUME":
            val = base + 120.0 * noise[i]
        else:  # FCR
            val = base + 0.8 * noise[i]
        points.append((d, round(float(val), 3)))
    return points


def _linear_fallback(values: list[float], horizon: int) -> list[float]:
    n = len(values)
    if n < 2:
        return [values[-1]] * horizon
    slope = (values[-1] - values[0]) / (n - 1)
    last = values[-1]
    return [last + slope * (k + 1) for k in range(horizon)]


def _future_dates(horizon: int) -> list[date]:
    return [_REFERENCE + timedelta(days=k) for k in range(horizon)]


def forecast(metric_key: str, horizon: int = 7) -> list[tuple[date, float]]:
    hist = get_history(metric_key)
    values = [v for _, v in hist]

    preds: list[float]
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        model = ExponentialSmoothing(values, trend="add", seasonal=None).fit()
        preds = [float(p) for p in model.forecast(horizon)]
        if any(math.isnan(p) or math.isinf(p) for p in preds):
            raise ValueError("non-finite forecast")
    except Exception:
        preds = _linear_fallback(values, horizon)

    # clip to sane bounds around the observed range to avoid wild extrapolation
    lo = min(values) * 0.5
    hi = max(values) * 1.5
    preds = [max(lo, min(hi, p)) for p in preds]

    return list(zip(_future_dates(horizon), [round(p, 3) for p in preds]))
