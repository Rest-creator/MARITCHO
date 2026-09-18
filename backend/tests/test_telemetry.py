import json
import logging
import sys

from app.core.telemetry import JSONLogFormatter, TraceIDFilter


def _make_record(msg="hello", level=logging.INFO, exc_info=None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="maricho-api",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    TraceIDFilter().filter(record)
    return record


def test_formatter_emits_valid_json_with_expected_keys():
    record = _make_record("job booked")

    formatted = JSONLogFormatter().format(record)
    payload = json.loads(formatted)

    assert payload["message"] == "job booked"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "maricho-api"
    assert "timestamp" in payload
    assert payload["trace_id"] == "0" * 32
    assert payload["span_id"] == "0" * 16
    assert "exception" not in payload


def test_formatter_includes_exception_when_present():
    try:
        raise ValueError("boom")
    except ValueError:
        record = _make_record("something failed", level=logging.ERROR, exc_info=sys.exc_info())

    payload = json.loads(JSONLogFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert "ValueError: boom" in payload["exception"]
