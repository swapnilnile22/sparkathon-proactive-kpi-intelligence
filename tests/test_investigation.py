from datetime import date, timedelta
from config import metric_by_key
from early_warning import PredictedAnomaly
import investigation
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


def test_stream_fallback_yields_all_layers():
    # use_bedrock=False exercises the synthetic fallback with no AWS calls
    got = list(stream_investigation(_anom(), metric_by_key("CSAT"), delay=0, use_bedrock=False))
    assert len(got) == 7
    assert got[0]["source"] == "fallback"


def test_focus_changes_the_brief():
    m = metric_by_key("CSAT")
    plain = build_layers(_anom(), m)[0]["content"]
    focused = build_layers(_anom(), m, focus={"label": "Thu Jul 16", "value": 3.98})[0]["content"]
    assert focused != plain
    assert "Thu Jul 16" in focused


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
