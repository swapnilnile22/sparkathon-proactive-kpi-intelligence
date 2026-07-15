from datetime import date, timedelta
from config import metric_by_key
from early_warning import evaluate, PredictedAnomaly

REF = date(2026, 7, 13)


def _pts(values):
    return [(REF + timedelta(days=i), float(v)) for i, v in enumerate(values)]


def test_higher_is_better_breach_detected():
    csat = metric_by_key("CSAT")  # target 4.0, higher_is_better
    fc = _pts([4.3, 4.2, 4.1, 3.9, 3.8, 3.7, 3.7])
    a = evaluate(csat, fc, REF)
    assert isinstance(a, PredictedAnomaly)
    assert a.first_breach_date == REF + timedelta(days=3)
    assert a.days_until == 3
    assert a.severity > 0
    assert len(a.breach_days) == 4


def test_lower_is_better_breach_detected():
    aht = metric_by_key("AHT")  # target 8.0, lower_is_better
    fc = _pts([7.0, 7.5, 8.5, 9.0, 9.0, 9.0, 9.0])
    a = evaluate(aht, fc, REF)
    assert a is not None
    assert a.first_breach_date == REF + timedelta(days=2)
    assert a.days_until == 2


def test_no_breach_returns_none():
    fcr = metric_by_key("FCR")  # target 75, higher_is_better
    fc = _pts([82, 81, 83, 80, 82, 81, 82])
    assert evaluate(fcr, fc, REF) is None
