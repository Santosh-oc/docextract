import json

import pytest

from app.vision.response_schema import ResponseParseError, parse_extraction_response


def test_parse_valid_json():
    raw = json.dumps({"fields": [{"name": "x", "value": "1", "confidence": 0.9, "page": 1, "evidence": "x: 1"}]})
    result = parse_extraction_response(raw)
    assert result.fields[0].name == "x"
    assert result.fields[0].confidence == 0.9


def test_parse_strips_markdown_fence():
    raw = "```json\n" + json.dumps({"fields": [{"name": "x", "value": None}]}) + "\n```"
    result = parse_extraction_response(raw)
    assert result.fields[0].value is None


def test_parse_missing_fields_key_raises():
    with pytest.raises(ResponseParseError):
        parse_extraction_response(json.dumps({"not_fields": []}))


def test_parse_invalid_json_raises():
    with pytest.raises(ResponseParseError):
        parse_extraction_response("this is not json at all")


def test_parse_confidence_out_of_range_raises():
    raw = json.dumps({"fields": [{"name": "x", "value": "1", "confidence": 1.5}]})
    with pytest.raises(ResponseParseError):
        parse_extraction_response(raw)


def test_parse_error_includes_raw_snippet():
    try:
        parse_extraction_response("not json")
    except ResponseParseError as exc:
        assert "not json" in exc.raw_snippet
    else:
        pytest.fail("expected ResponseParseError")
