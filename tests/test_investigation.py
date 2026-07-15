from datetime import date, timedelta
from config import metric_by_key
from early_warning import PredictedAnomaly
from investigation import build_layers, LAYER_ORDER, stream_investigation

REF = date(2026, 7, 13)


def _anom():
    return PredictedAnomaly(
        metric_key="CSAT",
        first_breach_date=REF + timedelta(days=3),
        days_until=3,
        severity=0.05,
        breach_days=[(REF + timedelta(days=3), 3.9)],
    )


def test_layers_cover_the_seven_names_in_order():
    layers = build_layers(_anom(), metric_by_key("CSAT"))
    assert [l["name"] for l in layers] == LAYER_ORDER
    assert len(LAYER_ORDER) == 7


def test_every_layer_has_content():
    for l in build_layers(_anom(), metric_by_key("CSAT")):
        assert l["title"]
        assert l["content"]


def test_narrative_is_future_framed():
    layers = build_layers(_anom(), metric_by_key("CSAT"))
    brief = layers[0]["content"].lower()
    assert "forecast" in brief or "predicted" in brief


def test_stream_yields_all_layers():
    got = list(stream_investigation(_anom(), metric_by_key("CSAT"), delay=0))
    assert len(got) == 7
