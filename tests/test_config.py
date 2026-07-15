from config import METRICS, metric_by_key, Metric


def test_four_board_metrics_present():
    keys = [m.key for m in METRICS]
    assert keys == ["CSAT", "AHT", "VOLUME", "FCR"]


def test_directions_are_valid():
    for m in METRICS:
        assert m.direction in ("higher_is_better", "lower_is_better")


def test_metric_by_key_returns_metric():
    m = metric_by_key("CSAT")
    assert isinstance(m, Metric)
    assert m.kpi_target == 4.0
    assert m.direction == "higher_is_better"


def test_metric_by_key_unknown_raises():
    try:
        metric_by_key("NOPE")
        assert False, "expected KeyError"
    except KeyError:
        pass
