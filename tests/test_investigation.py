from datetime import date, timedelta
from config import metric_by_key
from early_warning import PredictedAnomaly
import investigation
from investigation import build_layers, LAYER_ORDER, stream_investigation

REF = date(2026, 7, 16)
CSAT = metric_by_key("CSAT")
# a synthetic 7-day forecast (declining through the target)
FP = [(REF + timedelta(days=i), v) for i, v in enumerate([4.1, 4.06, 4.02, 3.98, 3.94, 3.90, 3.86])]


def _anom():
    return PredictedAnomaly(
        metric_key="CSAT",
        first_breach_date=REF + timedelta(days=3),
        days_until=3,
        severity=0.05,
        breach_days=[(REF + timedelta(days=3), 3.98), (REF + timedelta(days=4), 3.94)],
    )


def test_layers_cover_the_seven_names_in_order():
    layers = build_layers(CSAT, FP, anomaly=_anom())
    assert [l["name"] for l in layers] == LAYER_ORDER
    assert len(LAYER_ORDER) == 7


def test_every_layer_has_content_both_cases():
    for anomaly in (_anom(), None):
        for l in build_layers(CSAT, FP, anomaly=anomaly):
            assert l["title"]
            assert l["content"]


def test_at_risk_vs_on_track_titles_differ():
    at_risk = build_layers(CSAT, FP, anomaly=_anom())[0]["title"]
    on_track = build_layers(CSAT, FP, anomaly=None)[0]["title"]
    assert at_risk == "Predicted Anomaly"
    assert on_track == "Forecast Summary"


def test_narrative_is_future_framed():
    brief = build_layers(CSAT, FP, anomaly=_anom())[0]["content"].lower()
    assert "forecast" in brief or "predicted" in brief


def test_stream_fallback_yields_all_layers():
    got = list(stream_investigation(CSAT, FP, anomaly=_anom(), delay=0, use_bedrock=False))
    assert len(got) == 7
    assert got[0]["source"] == "fallback"


def test_on_track_stream_works_without_anomaly():
    got = list(stream_investigation(CSAT, FP, anomaly=None, delay=0, use_bedrock=False))
    assert len(got) == 7


def test_focus_changes_the_brief():
    plain = build_layers(CSAT, FP, anomaly=_anom())[0]["content"]
    focused = build_layers(CSAT, FP, anomaly=_anom(), focus={"label": "Sat Jul 19", "value": 3.98})[0]["content"]
    assert focused != plain
    assert "Sat Jul 19" in focused


def test_extract_json_strips_code_fences():
    raw = '```json\n{"layers": [{"name": "predicted_brief"}]}\n```'
    parsed = investigation._extract_json(raw)
    assert parsed["layers"][0]["name"] == "predicted_brief"


def test_validate_layers_rejects_wrong_order():
    bad = {"layers": [{"name": "financial_impact", "title": "x", "content": "y"}]}
    try:
        investigation._validate_layers(bad)
        assert False, "expected ValueError"
    except ValueError:
        pass
