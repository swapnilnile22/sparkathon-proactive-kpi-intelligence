from datetime import date
from config import METRICS
import forecast_data as fd


def test_history_is_deterministic_and_sized():
    a = fd.get_history("CSAT", days=14)
    b = fd.get_history("CSAT", days=14)
    assert a == b                      # deterministic
    assert len(a) == 14
    assert all(isinstance(v, float) for _, v in a)


def test_forecast_length_and_dates_start_today():
    fc = fd.forecast("CSAT", horizon=7)
    assert len(fc) == 7
    assert fc[0][0] == fd.reference_date()


def test_csat_forecast_breaches_target_within_horizon():
    fc = fd.forecast("CSAT", horizon=7)
    values = [v for _, v in fc]
    assert min(values) < 4.0           # hero scenario: CSAT dips below target


def test_healthy_metrics_stay_on_target():
    # AHT lower_is_better target 8.0 -> forecast should stay below 8
    aht = [v for _, v in fd.forecast("AHT", horizon=7)]
    assert max(aht) < 8.0
    # FCR higher_is_better target 75 -> forecast should stay above 75
    fcr = [v for _, v in fd.forecast("FCR", horizon=7)]
    assert min(fcr) > 75.0


def test_forecast_builds_for_every_metric():
    for m in METRICS:
        fc = fd.forecast(m.key, horizon=7)
        assert len(fc) == 7
